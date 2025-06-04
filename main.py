import argparse
import asyncio
from dotenv import load_dotenv

from manager import JobSearchManager

load_dotenv()

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Job Search Agent Manager")
    parser.add_argument(
        "-j", "--job_title", required=True,
        help="Job title to search for"
    )
    parser.add_argument(
        "-u", "--urls", nargs="+",
        help="Skip the search agent and run screening on provided URLs"
    )
    parser.add_argument(
        "-r", "--resume", dest="resume_path",
        help="File path to resume (for the screening agent)"
    )
    parser.add_argument(
        "-p", "--preferences", dest="preferences_path",
        help="File path to preferences (for the screening agent)"
    )
    parser.add_argument(
        "-n", "--top-n", dest="top_n", type=int,
        help="Only screen the first N URLs"
    )
    parser.add_argument(
        "-m", "--min-successful", dest="min_successful", type=int,
        help="Minimum number of successful job screenings desired; runs in batches until this threshold is met"
    )
    parser.add_argument(
        "-s", "--search-only", dest="search_only", action="store_true",
        help="Only run the search agent and output the URLs; skip screening"
    )
    parser.add_argument(
        "-o", "--output", dest="output_path", required=True,
        help="File path to write TSV results for screening outputs"
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    manager = JobSearchManager(
        job_title=args.job_title,
        resume_path=args.resume_path,
        preferences_path=args.preferences_path,
        urls=args.urls,
        top_n=args.top_n,
        search_only=args.search_only,
        min_successful=args.min_successful
    )
    results = await manager.run()
    if args.search_only:
        # Write URLs to output file, one per line
        with open(args.output_path, "w", encoding="utf-8") as f:
            for url in results.get("urls", []):
                f.write(url + "\n")
        return

    # Write formatted SummaryAgentOutput results
    failed = False
    with open(args.output_path, "w", encoding="utf-8") as f:
        f.write("="*80 + "\n" + "Job Search Results\n" + "="*80 + "\n\n")    
        for i, summary in enumerate(sorted(results, key=lambda x: 0 if x.fit_score is None else x.fit_score, reverse=True)):
            if not failed and summary.failed:
                failed = True
                f.write("\n\n" + "="*80 + "\n" + "Job Screening Failures\n" + "="*80 + "\n\n")            
            f.write(f"=====Job Result {i+1}=====\n")
            f.write(repr(summary) + "\n\n")
            

if __name__ == "__main__":
    asyncio.run(main())
