import logging
import math
from typing import List, Dict, Any, Optional, Tuple
from schemas.causal import TargetEvaluationResult
from schemas.interservice import FHIRLabEvolutionResponse
from clients.fhir_client import FHIRLabClient, fhir_lab_client
from clients.nhanes_client import NHANESBaselineClient, nhanes_client

logger = logging.getLogger(__name__)

class CausalInferenceEngine:
    """
    3-Layer Causal Inference Engine (DAGs) with strictly static clinical thresholds.
    Filters lifestyle confounders (Layer 1) from wearable signals (Layer 2)
    before recommending clinical laboratory investigations (Layer 3).
    """

    def __init__(
        self,
        fhir_client: Optional[FHIRLabClient] = None,
        nhanes_client_instance: Optional[NHANESBaselineClient] = None
    ):
        self.fhir_client = fhir_client or fhir_lab_client
        self.nhanes_client = nhanes_client_instance or nhanes_client

    async def evaluate_all_targets(
        self,
        patient_id: str,
        current_metric: Dict[str, Any],
        historical_records: List[Dict[str, Any]]
    ) -> List[TargetEvaluationResult]:
        """
        Executes causal disambiguation for the 4 Clinical Targets over a sliding window.
        historical_records should be ordered chronologically (oldest to newest).
        """
        results = []

        # Target 1: Deep Sleep Architecture (N3 < 16%)
        res_t1 = self.evaluate_target_1_deep_sleep(current_metric)
        results.append(res_t1)

        # Target 2: Metabolic Risk / Resting HR (>= 72 bpm) over 14-21 day window
        res_t2 = self.evaluate_target_2_metabolic_risk(current_metric, historical_records)
        results.append(res_t2)

        # Target 3: Systemic Inflammation / HRV RMSSD (< 38 ms) with 4-day persistence rule
        res_t3 = self.evaluate_target_3_inflammation_hrv(current_metric, historical_records)
        results.append(res_t3)

        # Target 4: Hematological Screening / Daytime Load Index (ICD) with FHIR Lab Retrospective Anchoring
        res_t4 = await self.evaluate_target_4_anemia_load(patient_id, current_metric)
        results.append(res_t4)

        return results

    # =========================================================================
    # TARGET 1: Sono Profundo (N3 < 16%) vs Volume de Passos & Álcool
    # =========================================================================
    def evaluate_target_1_deep_sleep(self, metric: Dict[str, Any]) -> TargetEvaluationResult:
        deep_pct = metric.get("sleep_stage_deep_pct")
        steps = metric.get("steps")
        alcohol_units = metric.get("alcohol_units") or 0.0
        waso_min = metric.get("waso_min") or 0.0

        target_id = "TARGET_1_DEEP_SLEEP"
        title = "1. Arquitetura do Sono (Sono Profundo N3 < 16%)"
        metric_desc = "Queda do percentual de sono profundo reparador (< 16% do total noturno)"

        # Normal condition
        if deep_pct is None or deep_pct >= 0.16:
            return TargetEvaluationResult(
                target_id=target_id,
                title=title,
                target_metric_description=metric_desc,
                is_anomaly=False,
                is_confounded=False,
                confounders_detected=[],
                mitigation_verdict="NORMAL",
                status_color="#34d399",  # Green
                protocol_applied="Monitoramento Contínuo da Arquitetura do Sono.",
                clinical_verdict="Sono profundo dentro dos parâmetros fisiológicos adequados (>= 16%).",
                trigger_alert=False
            )

        # Anomaly detected: deep_pct < 0.16
        confounders = []
        if steps is not None and steps < 6500:
            confounders.append("BAIXO_VOLUME_PASSOS_DIARIOS_MENOR_6500")
        if alcohol_units > 0.4 or waso_min > 45.0:
            confounders.append("CONSUMO_ALCOOL_FRAGMENTACAO_WASO")

        if confounders:
            protocol = (
                "Protocolo de Normalização Homeostática do Sono: "
                "O algoritmo não encaminha para suspeita de insônia primária ou neuroquímica se o "
                "volume locomotor mecânico estiver deprimido (< 6.500 passos) ou houver consumo de álcool. "
                "Prescrição: meta de 8.000 passos/dia por 14 dias e eliminação do álcool."
            )
            verdict = (
                "Queda de sono profundo explicada por hábitos cotidianos da Camada 1 "
                "(baixo gasto mecânico ou álcool na véspera). Falso alarme clínico mitigado com sucesso."
            )
            return TargetEvaluationResult(
                target_id=target_id,
                title=title,
                target_metric_description=metric_desc,
                is_anomaly=True,
                is_confounded=True,
                confounders_detected=confounders,
                mitigation_verdict="MITIGATED",
                status_color="#38bdf8",  # Informational Blue / Mitigated
                protocol_applied=protocol,
                clinical_verdict=verdict,
                trigger_alert=False
            )
        else:
            protocol = "Investigação de Distúrbio Primário do Sono / Apneia Obstrutiva."
            verdict = (
                "Queda atípica e não explicada de sono profundo (< 16%) mesmo com rotina ativa "
                "(>= 6.500 passos) e sem consumo de álcool. Recomenda-se avaliação médica / polissonografia."
            )
            return TargetEvaluationResult(
                target_id=target_id,
                title=title,
                target_metric_description=metric_desc,
                is_anomaly=True,
                is_confounded=False,
                confounders_detected=[],
                mitigation_verdict="CLINICAL_ANOMALY",
                status_color="#fbbf24",  # Warning Yellow
                protocol_applied=protocol,
                clinical_verdict=verdict,
                trigger_alert=True,
                alert_level="WARNING",
                recommended_loinc=None
            )

    # =========================================================================
    # TARGET 2: Risco Metabólico / FCR >= 72 bpm vs Tela Noturna & Cafeína
    # =========================================================================
    def evaluate_target_2_metabolic_risk(
        self,
        current_metric: Dict[str, Any],
        historical_records: List[Dict[str, Any]]
    ) -> TargetEvaluationResult:
        resting_hr = current_metric.get("resting_hr_bpm")
        screen_time = current_metric.get("screen_time_min") or 0.0
        caffeine_mg = current_metric.get("caffeine_mg") or 0.0

        target_id = "TARGET_2_METABOLIC_RISK"
        title = "2. Risco Metabólico & Triagem de Glicose / HbA1c (FCR >= 72 bpm)"
        metric_desc = "Frequência Cardíaca de Repouso basal elevada (>= 72 bpm)"

        if resting_hr is None or resting_hr < 72.0:
            return TargetEvaluationResult(
                target_id=target_id,
                title=title,
                target_metric_description=metric_desc,
                is_anomaly=False,
                is_confounded=False,
                confounders_detected=[],
                mitigation_verdict="NORMAL",
                status_color="#34d399",
                protocol_applied="Vigilância Metabólica Basal.",
                clinical_verdict="Frequência cardíaca de repouso dentro da faixa homeostática (< 72 bpm).",
                trigger_alert=False
            )

        # Anomaly detected today: resting_hr >= 72.0
        # Check Layer 1 confounders for today:
        confounders = []
        if screen_time > 130.0:
            confounders.append("TEMPO_TELA_NOTURNO_EXCESSIVO_MAIOR_130MIN")
        if caffeine_mg > 80.0:
            confounders.append("INGESTAO_CAFEINA_ELEVADA_MAIOR_80MG")

        # Rolling window analysis (trailing 14 to 21 days)
        window = historical_records[-21:] if historical_records else [current_metric]
        high_hr_days = [r for r in window if (r.get("resting_hr_bpm") or 0) >= 72.0]
        confounded_days = [
            r for r in high_hr_days
            if (r.get("screen_time_min") or 0) > 130.0 or (r.get("caffeine_mg") or 0) > 80.0
        ]
        
        pct_confounded = (len(confounded_days) / len(high_hr_days) * 100.0) if high_hr_days else 0.0

        protocol = (
            "Filtro de Janela Móvel de 14 a 21 Dias: O modelo suprime alertas de encaminhamento de curva glicêmica "
            "e hemoglobina glicada se o pico adrenérgico for pontual e decorrente de cafeína (> 80mg) ou tela (> 130min). "
            "Exame laboratorial indicado apenas se o desvio persistir com rotina regular e sem estimulantes."
        )

        if confounders or pct_confounded >= 50.0:
            verdict = (
                f"Elevação da FC de repouso ({resting_hr:.1f} bpm) moderada por estimulantes exógenos "
                f"({pct_confounded:.1f}% dos dias na janela explicados por tela noturna ou cafeína). "
                f"Falso alarme de risco metabólico mitigado."
            )
            return TargetEvaluationResult(
                target_id=target_id,
                title=title,
                target_metric_description=metric_desc,
                is_anomaly=True,
                is_confounded=True,
                confounders_detected=confounders or ["JANELA_MOVEL_MODERADA_POR_ESTIMULANTES"],
                mitigation_verdict="MITIGATED",
                status_color="#38bdf8",
                protocol_applied=protocol,
                clinical_verdict=verdict,
                trigger_alert=False
            )
        else:
            verdict = (
                f"Taquicardia basal de repouso persistente ({resting_hr:.1f} bpm) sem relação com tela ou cafeína "
                f"na janela de acompanhamento. Sugere-se dosagem de Glicose (LOINC 2345-7) e HbA1c (LOINC 4548-4)."
            )
            return TargetEvaluationResult(
                target_id=target_id,
                title=title,
                target_metric_description=metric_desc,
                is_anomaly=True,
                is_confounded=False,
                confounders_detected=[],
                mitigation_verdict="CLINICAL_ANOMALY",
                status_color="#fb7185",  # Red
                protocol_applied=protocol,
                clinical_verdict=verdict,
                trigger_alert=True,
                alert_level="WARNING",
                recommended_loinc="4548-4"
            )

    # =========================================================================
    # TARGET 3: Inflamação Sistêmica / HRV < 38 ms vs Noite Curta (< 6h) & Álcool
    # =========================================================================
    def evaluate_target_3_inflammation_hrv(
        self,
        current_metric: Dict[str, Any],
        historical_records: List[Dict[str, Any]]
    ) -> TargetEvaluationResult:
        hrv = current_metric.get("hrv_rmssd_ms")
        sleep_hours = current_metric.get("sleep_duration_hours") or 0.0
        alcohol_units = current_metric.get("alcohol_units") or 0.0

        target_id = "TARGET_3_INFLAMMATION_HRV"
        title = "3. Status Inflamatório Sistêmico (PCR-us) & HRV Autonômico"
        metric_desc = "Queda crítica da Variabilidade da Frequência Cardíaca (HRV RMSSD < 38 ms)"

        if hrv is None or hrv >= 38.0:
            return TargetEvaluationResult(
                target_id=target_id,
                title=title,
                target_metric_description=metric_desc,
                is_anomaly=False,
                is_confounded=False,
                confounders_detected=[],
                mitigation_verdict="NORMAL",
                status_color="#34d399",
                protocol_applied="Monitoramento do Tônus Parassimpático Autonômico.",
                clinical_verdict="HRV RMSSD dentro dos níveis normais de resiliência autonômica (>= 38 ms).",
                trigger_alert=False
            )

        # Anomaly detected: hrv < 38.0
        confounders = []
        if sleep_hours < 6.0:
            confounders.append("DEBITO_SONO_AGUDO_MENOR_6H")
        if alcohol_units > 0.4:
            confounders.append("CONSUMO_ALCOOL_RESSACA_AUTONOMICA")

        # 4 Consecutive Days Persistence Rule
        recent_days = historical_records[-4:] if historical_records else [current_metric]
        consecutive_low_hrv_count = 0
        consecutive_clean_days_count = 0

        for r in reversed(recent_days):
            r_hrv = r.get("hrv_rmssd_ms")
            r_sleep = r.get("sleep_duration_hours") or 0.0
            r_alc = r.get("alcohol_units") or 0.0

            if r_hrv is not None and r_hrv < 38.0:
                consecutive_low_hrv_count += 1
                if r_sleep >= 6.0 and r_alc <= 0.4:
                    consecutive_clean_days_count += 1
            else:
                break

        protocol = (
            "Critério de Persistência Temporal (Regra dos 4 Dias Consecutivos): "
            "O sistema descarta quedas transitórias de 24h a 72h após noites curtas (< 6h) ou ingestão de álcool. "
            "Apenas colapsos que persistam por >= 4 dias consecutivos sem privação de sono ativam sugestão de PCR-us."
        )

        if consecutive_clean_days_count >= 4:
            verdict = (
                f"Colapso persistente da HRV RMSSD ({hrv:.1f} ms) mantido por {consecutive_clean_days_count} dias "
                f"consecutivos com noites de sono adequadas (>= 6h) e sem álcool. Forte indício de sobrecarga autonômica "
                f"e inflamação sistêmica oculta. Recomenda-se dosagem de PCR-us (LOINC 30522-7) e Hemograma (LOINC 6690-2)."
            )
            return TargetEvaluationResult(
                target_id=target_id,
                title=title,
                target_metric_description=metric_desc,
                is_anomaly=True,
                is_confounded=False,
                confounders_detected=[],
                mitigation_verdict="CLINICAL_ANOMALY",
                status_color="#fb7185",  # Critical Red
                protocol_applied=protocol,
                clinical_verdict=verdict,
                trigger_alert=True,
                alert_level="CRITICAL",
                recommended_loinc="30522-7"
            )
        else:
            verdict = (
                f"Queda da HRV RMSSD ({hrv:.1f} ms) associada a estresse autonômico agudo ou privação circadiana "
                f"passageira (< 4 dias consecutivos limpos). Falso alarme de inflamação sistêmica mitigado."
            )
            return TargetEvaluationResult(
                target_id=target_id,
                title=title,
                target_metric_description=metric_desc,
                is_anomaly=True,
                is_confounded=True,
                confounders_detected=confounders or ["QUEDA_TRANSITORIA_MENOR_4_DIAS"],
                mitigation_verdict="MITIGATED",
                status_color="#818cf8",  # Indigo / Mitigated
                protocol_applied=protocol,
                clinical_verdict=verdict,
                trigger_alert=False
            )

    # =========================================================================
    # TARGET 4: Triagem de Anemia / FC Diurna > 92 bpm vs Carga / Cafeína
    # =========================================================================
    async def evaluate_target_4_anemia_load(
        self,
        patient_id: str,
        metric: Dict[str, Any]
    ) -> TargetEvaluationResult:
        avg_hr_day = metric.get("avg_hr_day_bpm")
        steps = metric.get("steps")
        caffeine_mg = metric.get("caffeine_mg") or 0.0

        target_id = "TARGET_4_ANEMIA_LOAD"
        title = "4. Triagem Hematológica (Hemoglobina / Ferritina)"
        metric_desc = "Taquicardia Diurna Desproporcional (> 92 bpm com < 6.000 passos / ICD elevado)"

        # Check basic criteria
        if avg_hr_day is None or avg_hr_day <= 92.0 or (steps is not None and steps >= 6000):
            return TargetEvaluationResult(
                target_id=target_id,
                title=title,
                target_metric_description=metric_desc,
                is_anomaly=False,
                is_confounded=False,
                confounders_detected=[],
                mitigation_verdict="NORMAL",
                status_color="#34d399",
                protocol_applied="Monitoramento da Eficiência de Transporte de Oxigênio.",
                clinical_verdict="Relação entre demanda locomotora e frequência cardíaca diurna adequada.",
                trigger_alert=False
            )

        # Anomaly detected: avg_hr_day > 92 and steps < 6000
        # Calculate ICD = HR_day / ln(steps + 1)
        safe_steps = max(int(steps or 0), 1)
        icd = round(float(avg_hr_day) / math.log(safe_steps + 1.0), 2)

        confounders = []
        if caffeine_mg > 90.0:
            confounders.append("INGESTAO_ALTA_CAFEINA_MAIOR_90MG")

        protocol = (
            "Ancoragem Retrospectiva no Banco de Dados FHIR: "
            "Calcula o Índice de Carga Diurna (ICD = FC_dia / ln(passos + 1)) e cruza assincronamente "
            "com os exames de sangue laboratoriais prévios (Ferritina LOINC 2276-4 e Hemoglobina LOINC 718-7). "
            "Se não houver histórico de anemia e o consumo de cafeína for alto, mitiga o alarme."
        )

        # Query FHIR Lab Service (Port 5000) for retrospective anchoring on Ferritin
        ferritin_lab: Optional[FHIRLabEvolutionResponse] = None
        try:
            ferritin_lab = await self.fhir_client.get_biomarker_evolution(patient_id, "2276-4")
        except Exception as e:
            logger.warning("Failed to query FHIR Lab for patient %s: %s", patient_id, e)

        prior_ferritin_borderline = False
        prior_ferritin_value = None

        if ferritin_lab and ferritin_lab.serie_temporal:
            latest_lab = ferritin_lab.serie_temporal[-1]
            prior_ferritin_value = latest_lab.valor_numerico
            if prior_ferritin_value is not None and prior_ferritin_value < 30.0:
                prior_ferritin_borderline = True
            elif latest_lab.status_classificacao in ("AMARELO", "VERMELHO"):
                prior_ferritin_borderline = True

        # Causal Disambiguation
        if caffeine_mg > 90.0 and not prior_ferritin_borderline:
            ferritin_note = (
                f"{prior_ferritin_value:.1f} ng/mL"
                if prior_ferritin_value is not None
                else "sem alteração prévia registrada"
            )
            verdict = (
                f"Taquicardia diurna ({avg_hr_day:.1f} bpm, ICD={icd:.2f}) associada ao consumo agudo de cafeína "
                f"({caffeine_mg:.0f} mg) em paciente sem histórico recente de deficiência de ferritina "
                f"(último valor: {ferritin_note}). Falso alarme mitigado com sucesso."
            )
            return TargetEvaluationResult(
                target_id=target_id,
                title=title,
                target_metric_description=metric_desc,
                is_anomaly=True,
                is_confounded=True,
                confounders_detected=confounders,
                mitigation_verdict="MITIGATED",
                status_color="#c084fc",  # Purple / Mitigated
                protocol_applied=protocol,
                clinical_verdict=verdict,
                trigger_alert=False
            )
        else:
            if prior_ferritin_borderline and prior_ferritin_value is not None:
                anchor_text = f"Ancoragem FHIR: Ferritina prévia limítrofe/baixa ({prior_ferritin_value:.1f} ng/mL)."
            elif prior_ferritin_borderline:
                anchor_text = "Ancoragem FHIR: Ferritina prévia sinalizada como limítrofe/alterada."
            elif prior_ferritin_value is not None:
                anchor_text = (
                    f"Ancoragem FHIR: último registro de Ferritina em {prior_ferritin_value:.1f} ng/mL "
                    "(taquicardia diurna sem justificativa por cafeína requer reavaliação hematológica)."
                )
            else:
                anchor_text = "Ancoragem FHIR: sem histórico recente de Ferritina disponível."

            verdict = (
                f"Esforço cardiovascular compensatório diurno desproporcional ({avg_hr_day:.1f} bpm com apenas "
                f"{steps or 0} passos; ICD={icd:.2f}) não justificado por cafeína. "
                f"{anchor_text} "
                f"Recomenda-se antecipar Hemograma Completo (LOINC 718-7) e Ferritina (LOINC 2276-4)."
            )
            return TargetEvaluationResult(
                target_id=target_id,
                title=title,
                target_metric_description=metric_desc,
                is_anomaly=True,
                is_confounded=False,
                confounders_detected=[],
                mitigation_verdict="CLINICAL_ANOMALY",
                status_color="#fb7185",
                protocol_applied=protocol,
                clinical_verdict=verdict,
                trigger_alert=True,
                alert_level="WARNING",
                recommended_loinc="2276-4"
            )

# Singleton causal engine instance
causal_engine = CausalInferenceEngine()

