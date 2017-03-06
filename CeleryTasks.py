from datetime import datetime
import sys
from celery import current_task
import util
from app import celery

@celery.task()
def probeStarLog(starLog):
    tid = probeStarLog.request.id
    starLog['time'] = util.getTime()
    starLog['log_header'] = util.concatStarLogHeader(starLog)
    found = False
    tries = 0
    started = datetime.now()
    lastCheckin = started

    while not found and tries < sys.maxint:
        starLog['nonce'] += 1
        starLog = util.hashStarLog(starLog)
        found = util.verifyDifficulty(int(starLog['difficulty']), starLog['hash'])
        now = datetime.now()
        if 1 < (now - lastCheckin).total_seconds():
            lastCheckin = now
            elapsedSeconds = (now - started).total_seconds()
            hashesPerSecond = tries / elapsedSeconds
            elapsedMinutes = elapsedSeconds / 60
            current_task.update_state(tid,state='PROGRESS', meta={'hashes_per_second': hashesPerSecond, 'elapsed_minutes': elapsedMinutes, 'tries': tries})
        tries += 1

    return found, starLog