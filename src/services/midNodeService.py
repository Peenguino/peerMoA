from src.utils.elabClassUtils import ElabClassUtils
from eclypse.remote.service import Service

class MidNodeService(Service, ElabClassUtils):

    def __init__(self, service_id, comm_interface = "mpi", store_step = False):
        super().__init__(service_id, comm_interface, store_step)
        
    async def step(self):
        self.logger.info(f"=====\n MidNodeService ID: {self._service_id} checking for messages... \n")
        receivedDict = await self.mpi.recv()
        self.logger.info(f"=====\n MidNodeService ID: {self._service_id} received: \n {receivedDict['originalPrompt']}")

        elaborated = await self.elab(receivedDict['originalPrompt'])
        self.logger.info(f"=====\n MidNodeService ID: {self._service_id} answered: {elaborated}\n")

        sentDict = {
            **receivedDict,
            "predictedAnswer": elaborated,
        }
        await self.mpi.bcast(sentDict)
        self.logger.info(f"=====\n MidNodeService ID: {self._service_id} sent: {sentDict['predictedAnswer']}\n")
