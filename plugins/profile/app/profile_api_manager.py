from app.api.v2.managers.base_api_manager import BaseApiManager
#from app.objects.c_profile import Profile


class ProfileApiManager(BaseApiManager):
    def __init__(self, data_svc, file_svc):
        super().__init__(data_svc=data_svc, file_svc=file_svc)
