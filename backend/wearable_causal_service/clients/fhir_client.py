import logging
from typing import Optional, Dict, Any
import httpx
from config import settings
from schemas.interservice import FHIRLabEvolutionResponse, FHIRObservationPoint, FHIRPatientInfo

logger = logging.getLogger(__name__)

class FHIRLabClient:
    """
    Asynchronous HTTP REST client for communicating with the FHIR Lab Service (Port 5000).
    Retrieves longitudinal laboratory observations categorized under HL7 FHIR and LOINC.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        self.base_url = (base_url or settings.FHIR_LAB_SERVICE_URL).rstrip("/")
        self.timeout = timeout or settings.HTTP_CLIENT_TIMEOUT_SEC

    async def get_biomarker_evolution(
        self, patient_id: str, codigo_loinc: str
    ) -> Optional[FHIRLabEvolutionResponse]:
        """
        Retrieves retrospective laboratory time-series for a patient and specific LOINC analyte.
        Key LOINC codes:
          - 2276-4: Ferritina sérica (ng/mL)
          - 718-7: Hemoglobina (g/dL)
          - 4548-4: Hemoglobina Glicada HbA1c (%)
          - 30522-7: Proteína C-Reativa ultrassensível (mg/L)
          - 2345-7: Glicose de jejum (mg/dL)
        """
        url = f"{self.base_url}/api/paciente/{patient_id}/evolucao/{codigo_loinc}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return FHIRLabEvolutionResponse.model_validate(data)
                elif response.status_code == 404:
                    logger.warning(
                        "No FHIR observations found for patient_id=%s, loinc=%s",
                        patient_id, codigo_loinc
                    )
                    return None
                else:
                    logger.error(
                        "FHIR Lab Service returned error %d: %s",
                        response.status_code, response.text
                    )
                    return None
        except httpx.RequestError as exc:
            logger.warning(
                "Unable to connect to FHIR Lab Service on port 5000 (%s). Error: %s",
                url, exc
            )
            return None

    async def get_patient_profile(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves patient demographic record (Patient resource)."""
        url = f"{self.base_url}/api/paciente/{patient_id}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.json()
                return None
        except httpx.RequestError as exc:
            logger.warning("Error querying patient profile from FHIR Lab Service: %s", exc)
            return None

# Singleton client instance
fhir_lab_client = FHIRLabClient()

