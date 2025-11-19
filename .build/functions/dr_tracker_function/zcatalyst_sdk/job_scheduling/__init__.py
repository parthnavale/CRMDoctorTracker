from typing import List, Union
from ..types import Component
from ._exception import CatalystJobSchedulingError
from .._http_client import AuthorizedHttpClient
from .._constants import RequestMethod, CredentialUser, Components
from .. import validator

from ._job import Job
from ._cron import Cron
from ._types import ICatalystJobpoolDetails


class JobScheduling(Component):
    def __init__(self, app) -> None:
        self._app = app
        self._requester = AuthorizedHttpClient(self._app)
        self.CRON = Cron(self) # pylint: disable=invalid-name
        self.JOB = Job(self) # pylint: disable=invalid-name

    def get_component_name(self) -> str:
        return Components.JOB_SCHEDULING

    def get_all_jobpool(self) -> List[ICatalystJobpoolDetails]:
        """
        Get details of all jobpool present

        Returns:
            List[Jobpool]: List of jobpool instances
        """
        resp = self._requester.request(
            method=RequestMethod.GET,
            path="/job_scheduling/jobpool",
            user=CredentialUser.ADMIN,
        )
        return resp.response_json.get("data")

    def get_jobpool(self, jobpool_id: Union[int, str]) -> ICatalystJobpoolDetails:
        """
        Get a jobpool's detail with the jobpool identifier

        Args:
            jobpool_id: name or id of the jobpool to be fetched

        Returns:
            Jobpool: Jobpool details fetched with the jobpool identifier

        Raises:
            Exception: If the jobpool_id is a invalid value
        """
        validator.is_non_empty_string_or_number(
            jobpool_id, "jobpool_id", CatalystJobSchedulingError
        )
        resp = self._requester.request(
            method=RequestMethod.GET,
            path=f"/job_scheduling/jobpool/{jobpool_id}",
            user=CredentialUser.ADMIN,
        )
        resp_json = resp.response_json
        return resp_json.get("data")
