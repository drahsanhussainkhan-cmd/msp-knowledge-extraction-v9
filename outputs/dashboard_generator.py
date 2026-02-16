"""
Dashboard Generator - Creates interactive HTML dashboards with Chart.js.
"""

import os
import json
from datetime import datetime
from collections import defaultdict


class DashboardGenerator:
    """Generates an interactive HTML dashboard for MSP extraction results."""

    def __init__(self, knowledge_db=None):
        self.knowledge_db = knowledge_db

    def generate(self, results, gaps, output_path):
        """Generate a complete HTML dashboard."""
        stats = self._compute_stats(results)
        gap_stats = self._compute_gap_stats(gaps)

        html = self._build_html(stats, gap_stats)

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Dashboard saved to {output_path}")
        return output_path

    def _compute_stats(self, results):
        """Compute dashboard statistics from results."""
        category_counts = defaultdict(int)
        doc_count = 0
        total = 0
        docs_data = {}

        if isinstance(results, dict):
            doc_count = len(results)
            for doc_name, doc_results in results.items():
                doc_total = 0
                if isinstance(doc_results, dict):
                    for category, items in doc_results.items():
                        if isinstance(items, list):
                            category_counts[category] += len(items)
                            total += len(items)
                            doc_total += len(items)
                docs_data[doc_name] = doc_total

        return {
            "total_documents": doc_count,
            "total_extractions": total,
            "category_counts": dict(category_counts),
            "docs_data": docs_data
        }

    def _compute_gap_stats(self, gaps):
        """Compute gap statistics."""
        if not gaps:
            return {"total": 0, "by_category": {}, "by_severity": {}}

        by_category = defaultdict(int)
        by_severity = defaultdict(int)
        for gap in gaps:
            cat = getattr(gap, "gap_category", None) or (gap.get("gap_category") if isinstance(gap, dict) else "unknown")
            sev = getattr(gap, "severity", None) or (gap.get("severity") if isinstance(gap, dict) else "unknown")
            by_category[cat] += 1
            by_severity[sev] += 1

        return {
            "total": len(gaps),
            "by_category": dict(by_category),
            "by_severity": dict(by_severity)
        }

    def _build_html(self, stats, gap_stats):
        """Build the full HTML dashboard."""
        cat_labels = json.dumps(list(stats["category_counts"].keys()))
        cat_values = json.dumps(list(stats["category_counts"].values()))
        gap_cat_labels = json.dumps(list(gap_stats["by_category"].keys()))
        gap_cat_values = json.dumps(list(gap_stats["by_category"].values()))
        gap_sev_labels = json.dumps(list(gap_stats["by_severity"].keys()))
        gap_sev_values = json.dumps(list(gap_stats["by_severity"].values()))

        severity_colors = {
            "critical": "#e74c3c",
            "important": "#f39c12",
            "minor": "#3498db"
        }
        sev_color_list = json.dumps([
            severity_colors.get(s, "#95a5a6") for s in gap_stats["by_severity"].keys()
        ])

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MSP Knowledge Extraction Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f6fa; color: #2c3e50; }}
  .header {{ background: linear-gradient(135deg, #0077b6, #023e8a); color: white; padding: 2rem; text-align: center; }}
  .header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
  .header p {{ opacity: 0.85; }}
  .container {{ max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
  .stat-card {{ background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center; }}
  .stat-card .number {{ font-size: 2rem; font-weight: 700; color: #0077b6; }}
  .stat-card .label {{ font-size: 0.9rem; color: #7f8c8d; margin-top: 0.3rem; }}
  .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
  .chart-card {{ background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
  .chart-card h3 {{ margin-bottom: 1rem; color: #34495e; }}
  canvas {{ max-height: 350px; }}
  .footer {{ text-align: center; padding: 2rem; color: #95a5a6; font-size: 0.85rem; }}
</style>
</head>
<body>
<div class="header">
  <h1>MSP Knowledge Extraction Dashboard</h1>
  <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</div>
<div class="container">
  <div class="stats-grid">
    <div class="stat-card"><div class="number">{stats['total_documents']}</div><div class="label">Documents</div></div>
    <div class="stat-card"><div class="number">{stats['total_extractions']}</div><div class="label">Extractions</div></div>
    <div class="stat-card"><div class="number">{len(stats['category_counts'])}</div><div class="label">Categories</div></div>
    <div class="stat-card"><div class="number">{gap_stats['total']}</div><div class="label">Gaps Found</div></div>
  </div>
  <div class="charts-grid">
    <div class="chart-card">
      <h3>Extractions by Category</h3>
      <canvas id="categoryChart"></canvas>
    </div>
    <div class="chart-card">
      <h3>Gaps by Category</h3>
      <canvas id="gapCategoryChart"></canvas>
    </div>
    <div class="chart-card">
      <h3>Gap Severity Distribution</h3>
      <canvas id="gapSeverityChart"></canvas>
    </div>
  </div>
</div>
<div class="footer">MSP Knowledge Extraction &amp; Decision Support System v2.0</div>
<script>
new Chart(document.getElementById('categoryChart'), {{
  type: 'bar',
  data: {{
    labels: {cat_labels},
    datasets: [{{ label: 'Extractions', data: {cat_values},
      backgroundColor: 'rgba(0,119,182,0.7)', borderColor: '#0077b6', borderWidth: 1 }}]
  }},
  options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }},
    scales: {{ y: {{ beginAtZero: true }}, x: {{ ticks: {{ maxRotation: 45 }} }} }} }}
}});
new Chart(document.getElementById('gapCategoryChart'), {{
  type: 'doughnut',
  data: {{
    labels: {gap_cat_labels},
    datasets: [{{ data: {gap_cat_values},
      backgroundColor: ['#e74c3c','#3498db','#2ecc71','#f39c12','#9b59b6','#1abc9c'] }}]
  }},
  options: {{ responsive: true }}
}});
new Chart(document.getElementById('gapSeverityChart'), {{
  type: 'pie',
  data: {{
    labels: {gap_sev_labels},
    datasets: [{{ data: {gap_sev_values}, backgroundColor: {sev_color_list} }}]
  }},
  options: {{ responsive: true }}
}});
</script>
</body>
</html>"""
