import json
from dataclasses import dataclass
from pathlib import Path

import settings
from context import PluginContext  # , GameState
from modules.lib.journal import JournalEntry
from modules.lib.module import Module

# Подключение функции перевода от EDMC
import l10n, functools                  # noqa e401
_translate = functools.partial(l10n.translations.tl, context=__file__)


@dataclass
class POIType:
    definition: dict[str, (str, int, float, bool)]
    body_field: str
    text: str
    category: str

    def matches(self, journal_entry: JournalEntry):
        return self._operation(self.definition, journal_entry.data)

    def _operation(self, definition: dict, data):
        operation = definition.get("operation")
        match operation:
            case "equal":
                if "field" in definition:
                    return data["field"] == definition["value"]
                return data == definition["value"]

            case "not equal":
                if "field" in definition:
                    return data["field"] != definition["value"]
                return data != definition["value"]

            case "greater":
                if "field" in definition:
                    return data["field"] > definition["value"]
                return data > definition["value"]

            case "greater or equal":
                if "field" in definition:
                    return data["field"] >= definition["value"]
                return data >= definition["value"]

            case "less":
                if "field" in definition:
                    return data["field"] < definition["value"]
                return data >= definition["value"]

            case "less or equal":
                if "field" in definition:
                    return data["field"] <= definition["value"]
                return data >= definition["value"]

            case "contains":
                if "field" in definition:
                    return definition["value"] in data["field"]
                return definition["value"] in data

            case "all":
                return all(
                    self._operation(definition["subcondition"], item)
                    for item in data[definition["field"]]
                )

            case "any":
                return any(
                    self._operation(definition["subcondition"], item)
                    for item in data[definition["field"]]
                )

            case "and":
                return all(
                    self._operation(condition, data)
                    for condition in definition["conditions"]
                )

            case "or":
                return all(
                    self._operation(condition, data)
                    for condition in definition["conditions"]
                )


class CustomPOIChecker(Module):
    CONFIG_FILENAME = "poi_criteria.json"

    def __init__(self):
        PluginContext.exp_visualizer.register(self)
        self.criteria = self.load_config()


    def load_config(self) -> dict[str, list[POIType]]:      # noqa e303
        config_file = Path(PluginContext.plugin_dir, "userdata", self.CONFIG_FILENAME)
        if not config_file.exists():
            PluginContext.logger.error("[POIChecker] POI criteria file not found.")
            PluginContext.notifier.send(_translate("POI criteria not found. Module disabled."))
            self.enabled = False
            return None

        try:
            with open(config_file, 'r', encoding="utf-8") as f:
                config: list[dict] = json.load(f)
                assert isinstance(config, list)
        except OSError as e:
            PluginContext.logger.error("[POIChecker] Couldn't access the POI criteria file.", exc_info=e)
            PluginContext.notifier.send(_translate("Couldn't access the POI criteria file. Module disabled."))
            self.enabled = False
            return None
        except (json.JSONDecodeError, AssertionError) as e:
            PluginContext.logger.error("[POIChecker] Couldn't decode POI criteria.", exc_info=e)
            PluginContext.notifier.send(_translate("Couldn't load POI criteria - file appears corrupted. Module disabled."))
            self.enabled = False
            return None

        criteria = dict()
        has_errors = False
        for poi_type in config:
            if not self._validate(poi_type):
                PluginContext.logger.warning(
                    f"[POIChecker] POI criteria is invalid. Raw entry: {json.dumps(poi_type, ensure_ascii=False)}"
                )
                has_errors = True
                continue

            event = poi_type["event"]
            if event not in criteria:
                criteria[event] = list()

            message = poi_type["message"]
            if message.get("category") not in settings.poi_categories:
                message["category"] = None

            poi = POIType(
                definition=poi_type["definition"],
                body_field=message["body_field"],
                text=message["text"],
                category=message["category"]
            )
            criteria[event].append(poi)

        if has_errors:
            PluginContext.notifier.send(_translate("Some POI criteria entries were found to be invalid and skipped."))
        return criteria


    def _validate(self, definition: dict, root = True):        # noqa e303
        if root:
            try:
                assert isinstance(definition.get("event"), str)
                assert isinstance(definition.get("message"), dict)
                message: dict = definition["message"]
                assert isinstance(message.get("body_field"), str)
                assert isinstance(message.get("text"), str)
                assert isinstance(definition.get("definition"), dict)
            except AssertionError:
                return False
            return self._validate(definition["definition"], False)

        try:
            assert isinstance(definition["operation"], str)
            operation = definition["operation"]
            match operation:
                case "equal" | "not equal" | "greater" | "greater or equal" | "less" | "less or equal" | "contains":
                    if "field" in definition:
                        assert isinstance(definition["field"], str)
                case "all" | "any":
                    assert isinstance(definition.get("field"), str)
                    assert isinstance(definition.get("subcondition"), dict)
                    return self._validate(definition["subcondition"], False)
                case "and" | "or":
                    assert isinstance(definition.get("conditions"), list)
                    conditions = definition["conditions"]
                    assert len(conditions) > 0
                    assert all(isinstance(c, dict) for c in conditions)
                    return all(self._validate(c, False) for c in conditions)
        except AssertionError:
            return False
        return True


    def on_journal_entry(self, entry: JournalEntry):      # noqa e303
        event = entry.data["event"]
        if event in self.criteria:
            for poi_type in self.criteria[event]:
                if poi_type.matches(entry):
                    PluginContext.exp_visualizer.show(
                        caller=self,
                        body=entry.data[poi_type.body_field],
                        text=poi_type.text,
                        category=poi_type.category
                    )
