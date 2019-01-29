excluded_events = [
    "Fileheader", 
    #"Music", 							#we should capture unknown music but maybe not all
    "Friends",
    "Cargo",
    "Loadout",
    "Materials",
    "LoadGame",
    "Rank",
    "Progress",
    "Location",
    "StartJump",   						# I think we should probably capture this but there will be a lot of records
    "SupercruiseEntry", 				# I think we should probably capture this but there will be a lot of records
    #"CommunityGoal",
    "USSDrop",  						# we are capturing this another way.
    "SupercruiseExit", 					# I think we should probably capture this but there will be a lot of records
    "FSDJump",							# I think we should probably capture this but there will be a lot of records
    "FuelScoop",
    "Scan",  							# do we really need this as it is captured by EDSM
    "MaterialDiscovered", 				# I don't think we need this 
    "MaterialCollected",				# We could capture this 
    "Screenshot",
    #"CollectCargo",					#This might depend on what kind of cargo
    "ReceiveText",
    "DockingRequested",
    "DockingGranted",
    "CommitCrime",
    "Docked",
    "RefuelAll",
    "SearchAndRescue",
    "PayFines",
    "ShipyardTransfer",
    "ModuleBuy",
    #"MissionAccepted",					# we want to capture this for refugee missions but
    "Undocked",
    "HeatWarning",
    #"Passengers", 						# I think we might wan this too
    "JetConeBoost",
    #"DataScanned",						#Probably should have a specific model for this
    "MissionRedirected",
    #"NavBeaconScan",					#This is interesting it give the number of bodies we shoudl see if it includes POIs
    "BuyDrones",
    "MaterialDiscarded",
    #"MissionCompleted", 				# I think we want this
    "RepairAll",
    "Repair",
	"Scanned",							#Doesnt appear to be anything interesting here but we could cature it when ist anything but Cargo or Crime in case they start recording alien scans 
    "ShieldState",
    "HullDamage",
    "ApproachSettlement",				#Doesnt seem very interesting
    "BuyAmmo",
    "PayLegacyFines",
    "SellExplorationData",				# Do we want to capture this? Could be useful for working out values
    "ModuleStore",					
    "MarketSell",
    "SellDrones",
    "ShipyardSwap",
    "ModuleRetrieve",
    "ModuleSellRemote",
    "FetchRemoteModule",
    "EjectCargo",
    #"Died",								# Can be used to record Tharghoid kills
    "Resurrect",
    "HeatDamage",
    "Interdicted",
    "Synthesis",
    "ModuleSwap",
    "SetUserShipName",
    "ShipyardBuy",
    "ShipyardNew",
    "ModuleSell",
    "EngineerCraft",
    "EngineerApply",
    "SendText",
    "Touchdown",
    "LaunchSRV",
    "DockSRV",
    "Liftoff",
    "MissionFailed",
    "DockingDenied",
    #"DatalinkScan",						# Capture this -- proimpt for form?
    "DatalinkVoucher",
    #"Bounty",							# thargoid bounties here
    "RedeemVoucher",
    "WingInvite",
    "WingJoin",
    "WingAdd",
    "WingLeave",
    "BuyExplorationData",
    "DockingTimeout",
    "Commander",
    "Reputation",
    "Missions",
    #"Statistics",    					# We should collect these in case now keys are added but we are interested in teh Thargoid Stats and should capture them independently
    "ShipTargeted",  					# Nothing here from teh Targoids
    "DiscoveryScan",					#EDSM Captures this
    "UnderAttack",						# not useful
    "Shipyard",
    "StoredShips",
    "Shutdown",
    "ApproachBody",
    "LeaveBody",
    "ModuleInfo",
    #"SystemsShutdown",					# This is when the thargoids do you with the shutdown field
    "Outfitting",
    "StoredModules",
    #"FactionKillBond",					# Thargoid kills!
    "RebootRepair",
    "SRVDestroyed",
    "RestockVehicle",
    "JoinACrew",
    "ChangeCrewRole",
    "QuitACrew",
    "LaunchDrone",
    "RepairDrone",
    "Market",
    "PayBounties",
    "Promotion",
    "EngineerProgress",
    "MaterialTrade",
    #"CommunityGoalJoin",				
    #"CommunityGoalReward",
    "MissionAbandoned",
    "CockpitBreached",
    "MarketBuy",
    "DockingCancelled",
    "TechnologyBroker",
    "CargoDepot",
    "CrewHire",
    "CrewAssign",
    "NpcCrewPaidWage",
    "LaunchFighter",
    "DockFighter",
    "FighterRebuilt",
    "FighterDestroyed",
    "NpcCrewRank",
    "VehicleSwitch"
]
