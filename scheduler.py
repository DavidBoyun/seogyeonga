"""
서경아 - 스케줄러
매일 자동으로 경매 데이터를 업데이트합니다.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SeogyeongaScheduler:
    """경매 데이터 자동 업데이트 스케줄러"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False

    def crawl_job(self):
        """크롤링 작업"""
        logger.info(f"[{datetime.now()}] 크롤링 작업 시작...")

        try:
            from crawler import SeogyeongaCrawler

            crawler = SeogyeongaCrawler()
            auctions = crawler.crawl_seoul_apartments(max_pages=3)

            if auctions:
                # DB에 저장
                count = crawler.save_to_db(auctions)
                logger.info(f"[{datetime.now()}] 크롤링 완료: {count}건 저장됨")
            else:
                logger.warning(f"[{datetime.now()}] 크롤링 결과 없음")

        except Exception as e:
            logger.error(f"[{datetime.now()}] 크롤링 실패: {e}")

    def start(self):
        """스케줄러 시작"""
        if self.is_running:
            logger.warning("스케줄러가 이미 실행 중입니다.")
            return

        # 매일 06:00, 18:00에 크롤링 실행
        self.scheduler.add_job(
            self.crawl_job,
            CronTrigger(hour=6, minute=0),
            id='crawl_morning',
            name='아침 크롤링 (06:00)',
            replace_existing=True
        )

        self.scheduler.add_job(
            self.crawl_job,
            CronTrigger(hour=18, minute=0),
            id='crawl_evening',
            name='저녁 크롤링 (18:00)',
            replace_existing=True
        )

        self.scheduler.start()
        self.is_running = True
        logger.info("스케줄러 시작됨 (06:00, 18:00 자동 크롤링)")

    def stop(self):
        """스케줄러 중지"""
        if not self.is_running:
            logger.warning("스케줄러가 실행 중이 아닙니다.")
            return

        self.scheduler.shutdown()
        self.is_running = False
        logger.info("스케줄러 중지됨")

    def run_now(self):
        """즉시 크롤링 실행"""
        logger.info("수동 크롤링 실행...")
        self.crawl_job()

    def get_next_run_time(self):
        """다음 실행 시간 조회"""
        jobs = self.scheduler.get_jobs()
        if not jobs:
            return None

        next_times = []
        for job in jobs:
            if job.next_run_time:
                next_times.append({
                    'job_name': job.name,
                    'next_run': job.next_run_time
                })

        return sorted(next_times, key=lambda x: x['next_run'])


# 전역 스케줄러 인스턴스
_scheduler = None


def get_scheduler():
    """스케줄러 인스턴스 반환"""
    global _scheduler
    if _scheduler is None:
        _scheduler = SeogyeongaScheduler()
    return _scheduler


def start_scheduler():
    """스케줄러 시작"""
    scheduler = get_scheduler()
    scheduler.start()
    return scheduler


def stop_scheduler():
    """스케줄러 중지"""
    scheduler = get_scheduler()
    scheduler.stop()


if __name__ == "__main__":
    import time

    print("=" * 50)
    print("  서경아 스케줄러 테스트")
    print("=" * 50)

    scheduler = get_scheduler()

    # 즉시 실행 테스트
    print("\n[테스트] 즉시 크롤링 실행...")
    scheduler.run_now()

    # 스케줄러 시작
    print("\n[테스트] 스케줄러 시작...")
    scheduler.start()

    # 다음 실행 시간 확인
    next_runs = scheduler.get_next_run_time()
    if next_runs:
        print("\n다음 실행 예정:")
        for run in next_runs:
            print(f"  - {run['job_name']}: {run['next_run']}")

    print("\n[테스트] 10초 대기 후 종료...")
    time.sleep(10)

    scheduler.stop()
    print("\n테스트 완료!")
