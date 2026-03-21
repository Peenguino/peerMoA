from eclypse.remote.service import Service

class InputNodeService(Service):

    def __init__(self, service_id, comm_interface = "mpi", store_step = False):
        super().__init__(service_id, comm_interface, store_step)

    async def step(self):
        self.logger.info(f"=====\n InputNodeService ID: {self._service_id} waiting for prompt... \n")
        receivedDict = await self.mpi.recv()
        self.logger.info(f"=====\n InputNodeService ID: {self._service_id} received prompt!\n\n {receivedDict['originalPrompt']} \n")

        # TODO: Ho inutilmente riscritto il count per eventuale gestione di reinvio nel layer
        sentDict = {
            **receivedDict,
            "count": 0
        }

        await self.mpi.bcast(sentDict)
        self.logger.info(f"=====\n InputNodeService ID: {self._service_id} sent prompt! \n")