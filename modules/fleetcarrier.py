from .lib.context import global_context
from .lib.module import Module
from .debug import debug

class FleetCarrierModule(Module):
    def on_journal_entry(self, entry):
        if entry.data["event"] == "Docked" and entry.data["StationType"] == "FleetCarrier":
            name = entry.data["StationName"]
            system = entry.data["StarSystem"]
            x, y, z = None, None, None
            global_context.cec_api.submit(
                method="PUT", 
                url=f"/api/triumvirate/v1/fc/{name}/system", 
                data={"name": system, "x": x, "y": y, "z": z}
            )
        elif entry.data["event"] == "CarrierJump":
            name = entry.data["StationName"]
            system = entry.data["StarSystem"]
            x, y, z = entry.data["StarPos"]
            global_context.cec_api.submit(
                method="PUT", 
                url=f"/api/triumvirate/v1/fc/{name}/system", 
                data={"name": system, "x": x, "y": y, "z": z}
            )
        elif entry.data["event"] == "Location" and entry.data["StationType"] == "FleetCarrier":
            name = entry.data["StationName"]
            system = entry.data["StarSystem"]
            x, y, z = entry.data["StarPos"]
            global_context.cec_api.submit(
                method="PUT", 
                url=f"/api/triumvirate/v1/fc/{name}/system", 
                data={"name": system, "x": x, "y": y, "z": z}
            )
