from pprint import pformat

from .lib.context import global_context
from .lib.module import Module
from .debug import debug

class FleetCarrierModule(Module):
    base_url = "/fc"
    def on_journal_entry(self, entry):
        event = entry.data["event"]
        if event == "Docked" and entry.data["StationType"] == "FleetCarrier":
            name = entry.data["StationName"]
            system = entry.data["StarSystem"]
            x, y, z = None, None, None
            global_context.cec_api.submit(
                method="PUT", 
                url=f"{self.base_url}/{name}/system", 
                data={"name": system, "x": x, "y": y, "z": z}
            )
        elif event == "CarrierJump":
            name = entry.data["StationName"]
            system = entry.data["StarSystem"]
            x, y, z = entry.data["StarPos"]
            global_context.cec_api.submit(
                method="PUT", 
                url=f"{self.base_url}/{name}/system", 
                data={"name": system, "x": x, "y": y, "z": z}
            )
        elif event == "Location" and entry.data["StationType"] == "FleetCarrier":
            name = entry.data["StationName"]
            system = entry.data["StarSystem"]
            x, y, z = entry.data["StarPos"]
            global_context.cec_api.submit(
                method="PUT", 
                url=f"{self.base_url}/{name}/system", 
                data={"name": system, "x": x, "y": y, "z": z}
            )
        elif event in {"CarrierJumpRequest", "CarrierJumpCancelled"} and not entry.is_beta:
            payload = dict(
                cmdr=entry.cmdr,
                is_beta=entry.is_beta,
                system=entry.system,
                station=entry.station,
                data=entry.data,
                state=entry.state
            )
            global_context.cec_api.submit(
                method="PUT",
                url=f"{self.base_url}/jump",
                data=payload
            )
