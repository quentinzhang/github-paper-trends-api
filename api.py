import requests
import json
import os
import re
import datetime
import logging
from bs4 import BeautifulSoup
import openai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

class GitHubPaperTrends:
    def __init__(self):
        self.base_url = "https://ghapi.huchen.dev"  # Using huchen's GitHub trending API
        self.github_api_url = "https://api.github.com"
        self.paper_keywords = ["paper", "research", "academic", "study", "algorithm", "survey", "thesis"]
        self.academic_domains = ["arxiv", "ieee", "acm", "springer", "science", "journal", "conference"]
    
    def get_trending_repositories(self, language=None, since="daily"):
        """Get trending repositories from GitHub"""
        url = f"{self.base_url}/repositories"
        params = {}
        if language:
            params['language'] = language
        if since:
            params['since'] = since
            
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching trending repositories: {e}")
            return []
    
    def is_academic_paper_repo(self, repo):
        """Check if repository is likely to be an academic paper"""
        # Check name and description for academic keywords
        name_lower = repo.get('name', '').lower()
        description_lower = repo.get('description', '').lower() if repo.get('description') else ''
        
        # Check for paper keywords in name or description
        has_paper_keyword = any(keyword in name_lower or keyword in description_lower for keyword in self.paper_keywords)
        
        # Check for academic domain references
        has_academic_domain = any(domain in name_lower or domain in description_lower for domain in self.academic_domains)
        
        # Check for PDF links in description
        has_pdf_link = 'pdf' in description_lower or '.pdf' in description_lower
        
        # Return True if at least two conditions are met
        return sum([has_paper_keyword, has_academic_domain, has_pdf_link]) >= 2
    
    def filter_academic_papers(self, repositories):
        """Filter repositories to get only academic papers"""
        return [repo for repo in repositories if self.is_academic_paper_repo(repo)]
    
    def get_repository_content(self, repo_url):
        """Get additional content like README from a repository"""
        try:
            # Extracting owner and repo name from the URL
            owner_repo = repo_url.replace('https://github.com/', '').split('/')
            if len(owner_repo) < 2:
                return {}
                
            owner = owner_repo[0]
            repo_name = owner_repo[1]
            
            # Get README content
            readme_url = f"{self.github_api_url}/repos/{owner}/{repo_name}/readme"
            response = requests.get(readme_url)
            
            if response.status_code == 200:
                content_data = response.json()
                if 'content' in content_data and content_data.get('encoding') == 'base64':
                    import base64
                    decoded_content = base64.b64decode(content_data['content']).decode('utf-8')
                    return {'readme': decoded_content}
            
            return {}
        except Exception as e:
            logger.error(f"Error fetching repository content: {e}")
            return {}
    
    def generate_paper_summary(self, repo, readme_content=""):
        """Generate a summary of the academic paper using OpenAI API"""
        if not OPENAI_API_KEY:
            logger.warning("OpenAI API key not set. Skipping summary generation.")
            return "Summary generation requires OpenAI API key."
        
        try:
            # Construct prompt for GPT
            prompt = f"""Please provide a concise academic summary of the following research paper. 
            Focus on the main contributions, methodology, and potential impact.
            
            Repository Name: {repo.get('name', '')}
            Author: {repo.get('author', '')}
            Description: {repo.get('description', '')}
            URL: {repo.get('url', '')}
            
            README Content: 
            {readme_content[:4000]}  # Limiting README content to avoid token limits
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You are an expert academic researcher who specializes in summarizing research papers. Provide clear, concise, and technically accurate summaries."}, 
                         {"role": "user", "content": prompt}],
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating paper summary: {e}")
            return "Failed to generate summary due to an error."
    
    def generate_daily_newsletter(self, papers, date=None):
        """Generate a daily newsletter of trending academic papers"""
        if not date:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        newsletter = f"# GitHub Trending Academic Papers - {date}\n\n"
        newsletter += "This newsletter highlights the trending academic papers on GitHub for today.\n\n"
        
        if not papers:
            newsletter += "No trending academic papers found for today.\n"
            return newsletter
        
        for i, paper in enumerate(papers, 1):
            newsletter += f"## {i}. {paper.get('name', 'Unnamed Paper')}\n\n"
            newsletter += f"**Author:** {paper.get('author', 'Unknown')}\n\n"
            newsletter += f"**Stars:** {paper.get('stars', 0)} | **Forks:** {paper.get('forks', 0)} | **Current Period Stars:** {paper.get('currentPeriodStars', 0)}\n\n"
            newsletter += f"**URL:** {paper.get('url', '')}\n\n"
            
            if paper.get('description'):
                newsletter += f"**Description:** {paper.get('description')}\n\n"
            
            if paper.get('summary'):
                newsletter += f"**Summary:**\n{paper.get('summary')}\n\n"
            
            newsletter += "---\n\n"
        
        newsletter += "*This newsletter is automatically generated by [GitHub Paper Trends API](https://github.com/quentinzhang/github-paper-trends-api).*\n"
        return newsletter

    def run_daily_update(self):
        """Run the daily update process to generate the newsletter"""
        try:
            # Get trending repositories
            logger.info("Fetching trending repositories...")
            trending_repos = self.get_trending_repositories(since="daily")
            
            # Filter academic papers
            logger.info("Filtering academic papers...")
            paper_repos = self.filter_academic_papers(trending_repos)
            
            # Get additional content and generate summaries
            logger.info(f"Found {len(paper_repos)} academic papers. Generating summaries...")
            paper_repos_with_summaries = []
            
            for repo in paper_repos[:10]:  # Limit to top 10 papers
                logger.info(f"Processing paper: {repo.get('name', '')}")
                repo_content = self.get_repository_content(repo.get('url', ''))
                readme_content = repo_content.get('readme', '')
                
                summary = self.generate_paper_summary(repo, readme_content)
                repo['summary'] = summary
                paper_repos_with_summaries.append(repo)
                logger.info(f"Summary generated for {repo.get('name', '')}")
            
            # Generate the newsletter
            logger.info("Generating newsletter...")
            newsletter = self.generate_daily_newsletter(paper_repos_with_summaries)
            
            # Save the newsletter
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            with open(f"newsletter-{date_str}.md", "w", encoding="utf-8") as f:
                f.write(newsletter)
            logger.info(f"Newsletter saved to newsletter-{date_str}.md")
            
            # Return data for the API
            return {
                "date": date_str,
                "papers": paper_repos_with_summaries,
                "newsletter": newsletter
            }
            
        except Exception as e:
            logger.error(f"Error running daily update: {e}")
            return {"error": str(e)}

# For testing
if __name__ == "__main__":
    paper_trends = GitHubPaperTrends()
    result = paper_trends.run_daily_update()
    print(json.dumps(result, indent=2))