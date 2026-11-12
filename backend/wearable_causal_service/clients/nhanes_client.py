import logging
from typing import Optional, Dict, Any
import httpx
from config import settings
from schemas.interservice import NHANESBaselineResponse, NHANESBaselineMetrics

logger = logging.getLogger(__name__)

class NHANESBaselineClient:
    """
    Asynchronous HTTP REST client for communicating with the NHANES Baseline Service (Port 5055).
    Retrieves CDC NHANES 15k population metrics and patient-specific 'Marco Zero' (Delta_ind) calibration.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        self.base_url = (base_url or settings.NHANES_BASELINE_SERVICE_URL).rstrip("/")
        self.timeout = timeout or settings.HTTP_CLIENT_TIMEOUT_SEC

    async def get_user_calibration(
        self, user_id: str, days: int = 14
    ) -> Optional[NHANESBaselineResponse]:
        """
        Retrieves calibrated resting heart rate baseline and individual offset (Delta_ind)
        calculated from the patient's initial wearable days.
        """
        url = f"{self.base_url}/api/wearables/user/{user_id}"
        params = {"days": days}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    # Map response to DTO safely
                    baseline_info = data.get("calibration", {}) or data.get("baseline", {})
                    metrics = NHANESBaselineMetrics(
                        expected_resting_hr_bpm=baseline_info.get("fc_esperada_bpm") or baseline_info.get("expected_resting_hr_bpm"),
                        delta_individual_bpm=baseline_info.get("delta_ind") or baseline_info.get("delta_individual_bpm"),
                        calibrated_r2=data.get("r2", 0.864)
                    )
                    return NHANESBaselineResponse(
                        user_id=user_id,
                        baseline_metrics=metrics,
                        risk_flags=data.get("risk_flags", {})
                    )
                elif response.status_code == 404:
                    logger.warning("User %s not found in NHANES Baseline Service", user_id)
                    return None
                else:
                    logger.error("NHANES Service returned error %d: %s", response.status_code, response.text)
                    return None
        except httpx.RequestError as exc:
            logger.warning(
                "Unable to connect to NHANES Baseline Service on port 5055 (%s). Error: %s",
                url, exc
            )
            return None

    async def get_patient_labs(self) -> Optional[Dict[str, Any]]:
        """Retrieves patient lab cross-check from NHANES bridge."""
        url = f"{self.base_url}/api/wearables/patient_labs"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.json()
                return None
        except httpx.RequestError as exc:
            logger.warning("Error querying patient labs from NHANES Baseline Service: %s", exc)
            return None

# Singleton client instance
nhanes_client = NHANESBaselineClient()

