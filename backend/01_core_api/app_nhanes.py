import os
import io
import csv
from flask import Flask, render_template, request, jsonify, Response
from data_engine import NhanesDataEngine
try:
    from wearable_bridge import WearableBridge
except ImportError:
    from nhanes_explorer.wearable_bridge import WearableBridge

app = Flask(__name__, template_folder="templates")

# Initialize engine on startup
engine = NhanesDataEngine()
wearable_bridge = WearableBridge(data_engine=engine)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/stats")
def api_stats():
    try:
        stats = engine.get_overview_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/patients")
def api_patients():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("pageSize", 20))
        search = request.args.get("search", "")
        gender = request.args.get("gender", "all")
        age_group = request.args.get("ageGroup", "all")
        bp_class = request.args.get("bpClass", "all")
        chol_class = request.args.get("cholClass", "all")
        req_blood = request.args.get("reqBlood", "false").lower() == "true"
        req_bp = request.args.get("reqBP", "false").lower() == "true"
        sort_by = request.args.get("sortBy", "SEQN")
        sort_dir = request.args.get("sortDir", "asc")

        result = engine.query_patients(
            page=page,
            page_size=page_size,
            search=search,
            gender=gender,
            age_group=age_group,
            bp_class=bp_class,
            chol_class=chol_class,
            req_blood=req_blood,
            req_bp=req_bp,
            sort_by=sort_by,
            sort_dir=sort_dir
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/patient/<int:seqn>")
def api_patient_detail(seqn):
    try:
        profile = engine.get_patient_profile(seqn)
        if profile is None:
            return jsonify({"error": f"Participante com ID {seqn} não encontrado."}), 404
        return jsonify(profile)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/patient/random")
def api_random_patient():
    try:
        profile = engine.get_random_patient()
        return jsonify(profile)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/correlations")
def api_correlations():
    try:
        var_x = request.args.get("var_x", "RIDAGEYR")
        var_y = request.args.get("var_y", "LBXTC")
        data = engine.get_correlation_data(var_x=var_x, var_y=var_y)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/codebook")
def api_codebook():
    try:
        return jsonify(engine.codebook)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/ml/insights")
def api_ml_insights():
    try:
        return jsonify(engine.ml_insights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/ml/predict", methods=["POST"])
def api_ml_predict():
    try:
        payload = request.get_json() or {}
        pred = engine.predict_heart_rate(payload)
        return jsonify({"predicted_pulse": pred})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/hormones/insights")
def api_hormone_insights():
    try:
        return jsonify(engine.hormone_insights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/hormones/predict", methods=["POST"])
def api_hormone_predict():
    try:
        payload = request.get_json() or {}
        pred = engine.predict_heart_rate_with_hormones(payload)
        return jsonify({"predicted_pulse": pred})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/anchored/insights")
def api_anchored_insights():
    try:
        return jsonify(engine.anchored_insights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/anchored/predict", methods=["POST"])
def api_anchored_predict():
    try:
        payload = request.get_json() or {}
        res = engine.predict_anchored_resting_hr(payload)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/export")
def api_export_csv():
    try:
        # Export filtered data as CSV
        search = request.args.get("search", "")
        gender = request.args.get("gender", "all")
        age_group = request.args.get("ageGroup", "all")
        bp_class = request.args.get("bpClass", "all")
        chol_class = request.args.get("cholClass", "all")
        req_blood = request.args.get("reqBlood", "false").lower() == "true"
        req_bp = request.args.get("reqBP", "false").lower() == "true"

        # Query all matching records up to 15560
        result = engine.query_patients(
            page=1,
            page_size=20000,
            search=search,
            gender=gender,
            age_group=age_group,
            bp_class=bp_class,
            chol_class=chol_class,
            req_blood=req_blood,
            req_bp=req_bp
        )

        items = result.get("items", [])
        if not items:
            return "Nenhum dado encontrado com os filtros selecionados.", 404

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(items[0].keys()))
        writer.writeheader()
        writer.writerows(items)

        csv_content = output.getvalue()
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=nhanes_filtered_cohort.csv"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/screening/cardio_blood/insights")
def api_cardio_blood_insights():
    try:
        return jsonify(engine.cardio_blood_insights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/screening/cardio_blood/predict", methods=["POST"])
def api_cardio_blood_predict():
    try:
        payload = request.get_json() or {}
        res = engine.predict_cardio_blood(payload)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/screening/metabolic/insights")
def api_metabolic_insights():
    try:
        return jsonify(engine.metabolic_insights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/screening/metabolic/predict", methods=["POST"])
def api_metabolic_predict():
    try:
        payload = request.get_json() or {}
        res = engine.predict_metabolic(payload)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/apnea/insights")
def api_apnea_insights():
    try:
        return jsonify(engine.apnea_insights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/apnea/predict", methods=["POST"])
def api_apnea_predict():
    try:
        payload = request.get_json() or {}
        res = engine.predict_apnea_hypoxia(payload)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/inflammatory/insights")
def api_inflammatory_insights():
    try:
        return jsonify(engine.inflammatory_insights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/inflammatory/predict", methods=["POST"])
def api_inflammatory_predict():
    try:
        payload = request.get_json() or {}
        res = engine.predict_inflammatory_autonomic(payload)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==============================================================
# CAMADA DE INFERÊNCIA & CALIBRAÇÃO (WEARABLES <-> NHANES)
# ==============================================================

@app.route("/wearables/sync", methods=["POST"])
@app.route("/api/wearables/sync", methods=["POST"])
def api_wearables_sync():
    """
    POST /wearables/sync
    Ponte que faz o modelo treinado no NHANES conversar com dados reais do wearable:
    - Mapeamento de Entrada: Lê a média dos últimos 7 a 14 dias (ex: resting_hr_bpm no lugar de BPXPLS).
    - Cálculo do Resíduo e Risco: Aplica a calibração individual (Delta_ind) e estima resíduo e scores.
    """
    try:
        payload = request.get_json() or {}
        user_id = payload.get("user_id")
        days = int(payload.get("days", payload.get("window_days", 14)))
        
        # Se recebeu user_id e faltam dados vitais, complementa com a janela real do CSV
        if user_id and "resting_hr_bpm" not in payload:
            window_metrics = wearable_bridge.get_user_window_metrics(user_id, days=days)
            window_metrics.update(payload)
            payload = window_metrics
            
        custom_labs = payload.get("labs")
        custom_delta = payload.get("delta_ind")
        
        result = wearable_bridge.run_inference_and_calibration(
            wearable_payload=payload,
            custom_labs=custom_labs,
            custom_delta_ind=custom_delta
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/wearables/users")
def api_wearables_users():
    """Retorna lista de usuários de amostra do dataset de wearables."""
    try:
        limit = int(request.args.get("limit", 25))
        users = wearable_bridge.get_available_users(limit=limit)
        return jsonify({"users": users, "total": len(users)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/wearables/user/<user_id>")
def api_wearables_user_inference(user_id):
    """Executa a inferência e calibração automática para um usuário específico dos wearables."""
    try:
        days = int(request.args.get("days", 14))
        metrics = wearable_bridge.get_user_window_metrics(user_id, days=days)
        result = wearable_bridge.run_inference_and_calibration(metrics)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/wearables/patient_labs")
def api_wearables_patient_labs():
    """Retorna os exames clínicos mais recentes do paciente (banco open_health.db)."""
    try:
        labs = wearable_bridge.get_latest_patient_labs()
        return jsonify(labs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    print(f"\n==================================================")
    print(f" NHANES Analytics Explorer is running on:")
    print(f" http://localhost:{port}")
    print(f"==================================================\n")
    app.run(host="127.0.0.1", port=port, debug=False)
