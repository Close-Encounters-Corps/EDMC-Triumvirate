import sys
import types
from typing import TYPE_CHECKING

from Triumvirate.core.context import PluginContext


def _translate(x: str, lang: str | None = None) -> str:
    filename = sys._getframe(1).f_code.co_filename
    return PluginContext._tr_template(x=x, filepath=filename, lang=lang)


if TYPE_CHECKING:
    debug = PluginContext.logger.debug
    info = PluginContext.logger.info
    warning = PluginContext.logger.warning
    error = PluginContext.logger.error
    critical = PluginContext.logger.critical
else:
    # Вэлком в мою нерегулярную рубрику "Фантастические твари и что они наворотили в EDMC"!
    # EDMCLogging.py в их коде реализует кастомный формат логгера:
    # `[UTC TIME] - [LEVEL] - <plugins>.EDMC-Triumvirate.Triumvirate.modules.squadron.SquadronTracker.__init__:23: <message>`
    # который, однако, успешно ломается при любом использовании logging.Logger.<level> не напрямую,
    # потому что EDCD игнорят параметр stacklevel в своих махинациях, из-за чего при использовании функций-обёрток
    # ихнее форматирование радостно пропишет путь именно к этим обёрткам.
    # Две проблемы, которые решены здесь:
    # 1) qualname (то есть конечное название функции/метода, из которого идёт вызов): мы явно передаём правильное,
    #    чтобы не писалось просто "debug".
    # 2) Путь к файлу: его в extra передавать бесполезно, потому что EDCD каким-то наколеночным кодом разворачивают
    #    стек и ищут первый фрейм, где локальная переменная self не будет инстансом logging.Logger, после чего
    #    берут __name__ этого фрейма. Передавая во wrapper параметр self вместо использования импортированного
    #    PluginContext.logger напрямую мы, по сути, заставляем тот их код подумать, что этот фрейм всё ещё принадлежит
    #    кишочкам библиотеки logging и проскочить его. Хак? Да. Ненадёжно? Ищщо как! Но пока что работает.
    def __make_logger_proxy(level_name: str):
        def wrapper(self, *args, **kwargs):
            kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
            extra = kwargs.setdefault("extra", {})
            extra["qualname"] = sys._getframe(1).f_code.co_qualname
            return getattr(self, level_name)(*args, **kwargs)
        return types.MethodType(wrapper, PluginContext.logger)

    debug = __make_logger_proxy("debug")
    info = __make_logger_proxy("info")
    warning = __make_logger_proxy("warning")
    error = __make_logger_proxy("error")
    critical = __make_logger_proxy("critical")
