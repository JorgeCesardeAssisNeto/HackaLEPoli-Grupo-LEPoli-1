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
                    # Suporta formato real da porta 5055 ("calibration_and_residuals") e mocks ("calibration"/"baseline")
                    baseline_info = (
                        data.get("calibration_and_residuals")
                        or data.get("calibration")
                        or data.get("baseline")
                        or {}
                    )
                    expected_hr = (
                        baseline_info.get("expected_pulse_nhanes")
                        if baseline_info.get("expected_pulse_nhanes") is not None
                        else (baseline_info.get("fc_esperada_bpm") if baseline_info.get("fc_esperada_bpm") is not None
                              else baseline_info.get("expected_resting_hr_bpm"))
                    )
                    delta_ind = (
                        baseline_info.get("delta_individual_bpm")
                        if baseline_info.get("delta_individual_bpm") is not None
                        else baseline_info.get("delta_ind")
                    )
                    calibrated_r2 = (
                        data.get("r2")
                        if data.get("r2") is not None
                        else baseline_info.get("r2")
                    )
                    metrics = NHANESBaselineMetrics(
                        expected_resting_hr_bpm=expected_hr,
                        delta_individual_bpm=delta_ind,
                        calibrated_r2=calibrated_r2,
                    )
                    risk_flags = data.get("risk_flags") or data.get("models_inference") or {}
                    return NHANESBaselineResponse(
                        user_id=data.get("wearable_window", {}).get("user_id") or user_id,
                        patient_id=data.get("patient_id"),
                        baseline_metrics=metrics,
                        risk_flags=risk_flags,
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

