import os
import psycopg2
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from parallel import Parallel
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# INITIALIZE PARALLEL CLIENT
api_key = os.environ.get("PARALLEL_API_KEY")
if not api_key:
    raise ValueError("PARALLEL_API_KEY environment variable is required")
client = Parallel(api_key=api_key)

# DATABASE CONNECTION HELPER
def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    return psycopg2.connect(database_url)




@app.route("/")
def index():
    """SERVE MAIN SEARCH PAGE"""
    return render_template("index.html")


@app.route("/evaluations")
def evaluations_page():
    """SERVE EVALUATIONS HISTORY PAGE"""
    return render_template("evaluations.html")


@app.route("/api/search", methods=["POST"])
def search():
    """EXECUTE SEARCH USING PARALLEL API"""
    try:
        data = request.get_json()
        objective = data.get("objective")
        search_queries = data.get("search_queries")
        mode = data.get("mode", "one-shot")
        
        if not objective:
            return jsonify({"error": "Objective is required"}), 400
        
        if mode not in ["one-shot", "agentic"]:
            return jsonify({"error": "Mode must be 'one-shot' or 'agentic'"}), 400
        
        # EXECUTE SEARCH
        search_response = client.beta.search(
            objective=objective,
            search_queries=search_queries,
            mode=mode,
            max_results=10
        )
        
        # FORMAT RESULTS FOR FRONTEND
        results = []
        for result in search_response.results:
            results.append({
                "url": result.url,
                "title": result.title,
                "publish_date": result.publish_date,
                "excerpts": result.excerpts or []
            })
        
        return jsonify({
            "search_id": search_response.search_id,
            "results": results
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    """SAVE EVALUATION FEEDBACK"""
    try:
        data = request.get_json()
        search_id = data.get("search_id")
        result_url = data.get("result_url")
        result_title = data.get("result_title")
        is_correct = data.get("is_correct")
        query = data.get("query")
        mode = data.get("mode", "one-shot")
        
        if not all([search_id, result_url, is_correct is not None, query]):
            return jsonify({"error": "Missing required fields"}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO evaluations (search_id, query, mode, result_url, result_title, is_correct)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (search_id, query, mode, result_url, result_title, is_correct))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Evaluation saved"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/evaluations", methods=["GET"])
def get_evaluations():
    """RETRIEVE PAST EVALUATIONS"""
    try:
        limit = request.args.get("limit", 100, type=int)
        offset = request.args.get("offset", 0, type=int)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # GET STATISTICS
        cur.execute("""
            SELECT mode, is_correct, COUNT(*) as count
            FROM evaluations
            GROUP BY mode, is_correct
        """)
        
        stats_rows = cur.fetchall()
        statistics = {
            "agentic": {"correct": 0, "incorrect": 0},
            "one-shot": {"correct": 0, "incorrect": 0}
        }
        
        for row in stats_rows:
            mode = row[0]
            is_correct = row[1]
            count = row[2]
            if mode in statistics:
                if is_correct:
                    statistics[mode]["correct"] = count
                else:
                    statistics[mode]["incorrect"] = count
        
        # GET EVALUATIONS
        cur.execute("""
            SELECT id, search_id, query, mode, result_url, result_title, is_correct, created_at
            FROM evaluations
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        rows = cur.fetchall()
        evaluations = []
        for row in rows:
            evaluations.append({
                "id": row[0],
                "search_id": row[1],
                "query": row[2],
                "mode": row[3],
                "result_url": row[4],
                "result_title": row[5],
                "is_correct": row[6],
                "created_at": row[7].isoformat() if row[7] else None
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            "statistics": statistics,
            "evaluations": evaluations
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)

