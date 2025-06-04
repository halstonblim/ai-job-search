import argparse
import asyncio
import logging
from datetime import datetime
from pathlib import Path
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
        "-d", "--desired-count", dest="desired_count", type=int,
        help="Desired number of successful job screenings"
    )
    parser.add_argument(
        "-s", "--search-only", dest="search_only", action="store_true",
        help="Only run the search agent and output the URLs; skip screening"
    )
    parser.add_argument(
        "-o", "--output", dest="output_path", required=True,
        help="File path to write TSV results for screening outputs"
    )
    parser.add_argument(
        "-l", "--log", dest="log_path",
        help="File path to write logs"
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    # Setup logging
    log_path = args.log_path
    if not log_path:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = args.job_title.strip().lower().replace(" ", "_")
        log_path = log_dir / f"{slug}_{timestamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filename=str(log_path),
        filemode="w",
    )

    logging.info(f"CLI arguments: {args}")

    manager = JobSearchManager(
        job_title=args.job_title,
        resume_path=args.resume_path,
        preferences_path=args.preferences_path,
        urls=args.urls,
        desired_count=args.desired_count,
        search_only=args.search_only
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

        report = manager.compile_report(results)
        f.write(report + "\n")
            

if __name__ == "__main__":
    asyncio.run(main())
