"""
Инструменты для работы с BGS.
"""
from datetime import datetime

import settings
from l10n import Locale

from ..debug import debug, error
from ..lib.context import global_context
from ..lib.spreadsheet import Spreadsheet
from ..systems import Systems
from .patrol import build_patrol

EXCLUDE = {"Basta", "Hide", "Cancel"}

class BGSTasksOverride:
    """
    Замена PatrolModule.getBGSOveride.
    """

    def __init__(self, patrols, systems):
        self.patrols = patrols
        self.systems = systems

    @classmethod
    def new(cls, SQID):
        url = settings.bgs_tasks_url
        spreadsheet = Spreadsheet(url)
        patrols, systems_override = [], []
        for row in spreadsheet:
            squadron, system, x, y, z, TINF, TFAC, Description = row
            instructions = Description.format(TFAC, TINF)
            
            if Description in EXCLUDE:
                continue

            if squadron == SQID:
                systems_override.append(system)
                item = build_patrol(
                    "BGSO",
                    system,
                    (float(x), float(y), float(z)),
                    instructions,
                    None,
                    None,
                )

                patrols.append(item)


        return cls(patrols, systems=systems_override)


def new_bgs_patrol(bgs, faction, override):
    system = bgs.get("system_name")
    if system in override:
        return
    return build_patrol(
        type="BGS",
        system=system,
        coords=Systems.edsmGetSystem(system),
        instructions=get_bgs_instructions(bgs, faction),
        url="https://elitebgs.app/system/{}".format(bgs.get("system_id")),
    )


def get_bgs_instructions(bgs, faction):
    from .patrol_module import PatrolModule
    patrol = global_context.by_class(PatrolModule)
    target = 0.50 <= float(bgs.get("influence")) <= 0.65
    over = float(bgs.get("influence")) > 0.65
    under = float(bgs.get("influence")) < 0.50

    active_states = patrol.getStates("active_states", bgs)
    states = ""
    if active_states:
        statesraw = active_states.split(",")
        states = ", ".join(statesraw)

    # 2019-03-24T11:14:38.000Z
    d1 = datetime.strptime(bgs.get("updated_at"), "%Y-%m-%dT%H:%M:%S.%fZ")
    d2 = datetime.now()

    last_updated = (d2 - d1).days
    if last_updated == 0:
        update_text = ""
    elif last_updated == 1:
        update_text = ". Данные обновлены 1 день назад"
    elif last_updated < 7:
        update_text = ". Последнее обновление данных {} дней назад".format(
            last_updated
        )
    elif last_updated > 6:
        update_text = ". Последнее обновление данных {} дней назад. Пожалуйста прыгните в эту систему что бы обновить данные".format(
            last_updated
        )

    if faction == "Close Encounters Corps":
        contact = "Пожалуйста, свяжитесь с AntonyVern [СЕС]#5904 на сервере СЕС для получения инструкций"
    if faction == "EG Union":
        contact = "Пожалуйста, свяжитесь с HEúCMuT#1242 на сервере EGP для получения инструкций"
    if faction == "Royal Phoenix Corporation":
        contact = "Пожалуйста, свяжитесь с Saswitz#9598 на сервере RPSG для получения инструкций"
    if target:
        retval = "{} Влияние {}%;{}{}".format(
            faction,
            Locale.stringFromNumber(float(bgs.get("influence") * 100), 2),
            states,
            update_text,
        )
    if over:
        retval = "{} Влияние {}%;{} {}{}.".format(
            faction,
            Locale.stringFromNumber(float(bgs.get("influence") * 100), 2),
            states,
            contact,
            update_text,
        )
    if under:
        retval = "{} Влияние {}%;{} Пожалуйста выполняйте миссии за {}, чтобы увеличить наше влияние {}".format(
            faction,
            Locale.stringFromNumber(float(bgs.get("influence") * 100), 2),
            states,
            faction,
            update_text,
        )

    debug("[patrol.bgs] System {}: {}".format(bgs.get("system_name"), retval))
    return retval
