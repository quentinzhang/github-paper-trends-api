from flask import Flask, jsonify, request, render_template, send_file
import os
import json
import datetime
from api import GitHubPaperTrends

app = Flask(__name__)
paper_trends = GitHubPaperTrends()

# Cache for storing the latest newsletter results
cache = {
    'last_update': None,
    'data': None,
    'newsletter_path': None
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/trending-papers')
def get_trending_papers():
    # Get query parameters
    language = request.args.get('language')
    since = request.args.get('since', 'daily')  # Default to daily
    
    # Get trending repositories
    trending_repos = paper_trends.get_trending_repositories(language, since)
    
    # Filter academic papers
    paper_repos = paper_trends.filter_academic_papers(trending_repos)
    
    return jsonify({
        'count': len(paper_repos),
        'papers': paper_repos
    })

@app.route('/api/summarize-paper')
def summarize_paper():
    # Get query parameters
    repo_url = request.args.get('repo_url')
    
    if not repo_url or not repo_url.startswith('https://github.com/'):
        return jsonify({
            'error': 'Invalid GitHub repository URL'
        }), 400
    
    # For demo purposes, create a mock repository structure
    repo_parts = repo_url.replace('https://github.com/', '').split('/')
    if len(repo_parts) < 2:
        return jsonify({
            'error': 'Invalid GitHub repository URL format'
        }), 400
    
    repo = {
        'name': repo_parts[1],
        'author': repo_parts[0],
        'url': repo_url,
        'description': request.args.get('description', '')
    }
    
    # Get repository content
    repo_content = paper_trends.get_repository_content(repo_url)
    readme_content = repo_content.get('readme', '')
    
    # Generate summary
    summary = paper_trends.generate_paper_summary(repo, readme_content)
    
    return jsonify({
        'repo': repo,
        'summary': summary
    })

@app.route('/api/newsletter')
def get_latest_newsletter():
    # Check if we need to update the cache
    now = datetime.datetime.now()
    today = now.date()
    
    if cache['last_update'] is None or cache['last_update'].date() != today:
        # Run daily update
        result = paper_trends.run_daily_update()
        
        # Update cache
        cache['last_update'] = now
        cache['data'] = result
        
        # Save newsletter to file
        date_str = now.strftime("%Y-%m-%d")
        newsletter_path = f"newsletter-{date_str}.md"
        with open(newsletter_path, "w", encoding="utf-8") as f:
            f.write(result['newsletter'])
        cache['newsletter_path'] = newsletter_path
    
    # Return data from cache
    return jsonify(cache['data'])

@app.route('/api/newsletter/download')
def download_newsletter():
    # Get or generate the latest newsletter
    if cache['newsletter_path'] is None or not os.path.exists(cache['newsletter_path']):
        get_latest_newsletter()
    
    if cache['newsletter_path'] and os.path.exists(cache['newsletter_path']):
        return send_file(cache['newsletter_path'], as_attachment=True)
    else:
        return jsonify({
            'error': 'Newsletter file not found'
        }), 404

# Endpoint for manually triggering a refresh
@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    try:
        result = paper_trends.run_daily_update()
        
        # Update cache
        cache['last_update'] = datetime.datetime.now()
        cache['data'] = result
        
        # Save newsletter to file
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        newsletter_path = f"newsletter-{date_str}.md"
        with open(newsletter_path, "w", encoding="utf-8") as f:
            f.write(result['newsletter'])
        cache['newsletter_path'] = newsletter_path
        
        return jsonify({
            'status': 'success',
            'message': 'Data refreshed successfully',
            'data': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error refreshing data: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)