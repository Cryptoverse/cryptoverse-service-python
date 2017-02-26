from app import app
from datetime import datetime
from multiprocessing import Process, Queue
import multiprocessing
import sys
import util
import copy
import time

def probeStarLog(starLog):
	app.logger.info('ps count: %s' % (multiprocessing.cpu_count()))
	processCount = 8
	minNonce = starLog['nonce']
	maxNonce = sys.maxint - minNonce
	nonceRange = (maxNonce - minNonce) / processCount
	processes = list()

	totalTries = 0
	found = False
	validNonce = 0

	started = datetime.now()
	queue = Queue()

	for i in range(0, processCount):
		start = minNonce + (i * nonceRange)
		end = start + nonceRange
		process = Process(target=probeStarLogWorker, args=(i, queue, copy.deepcopy(starLog), start, end))
		processes.append(process)
		process.start()
		time.sleep(0.1)

	delay = 60
	while not found:
		time.sleep(delay)
		while not queue.empty():
			try:
				entry = queue.get_nowait()
				if isinstance(entry[0], int):
					totalTries += entry[0]
				elif isinstance(entry[0], bool):
					found = True
					validNonce = entry[1]
			except:
				traceback.print_exc()
				pass
		
		now = datetime.now()
		elapsedSeconds = (now - started).total_seconds()
		hashesPerSecond = totalTries / elapsedSeconds
		elapsedMinutes = elapsedSeconds / 60
		app.logger.info('%.1f minutes elapsed, %s hashes at %s per second' % (elapsedMinutes, '{:,}'.format(totalTries), '{:,.2f}'.format(hashesPerSecond)))

	app.logger.info(('Found! Nonce: %s' % (validNonce)) if localFound else 'Not found!')


def probeStarLogWorker(id, queue, starLog, startNonce, endNonce):
	hash = ''
	found = False
	tries = 0
	started = datetime.now()
	lastCheckin = started
	lastTries = 0
	while not found and tries < (endNonce - startNonce):
		starLog['nonce'] = startNonce + tries
		starLog = util.hashStarLog(starLog)
		found = util.verifyDifficulty(starLog['difficulty'], starLog['hash'])
		now = datetime.now()
		if 50 < (now - lastCheckin).total_seconds():
			lastCheckin = now
			tryDelta = tries - lastTries
			try:
				queue.put_nowait([tryDelta])
				lastTries = tries
			except:
				pass
		tries += 1
		
	if found:
		app.logger.info('Found! %s tries to found nonce %s producing %s' % (tries, starLog['nonce'], starLog['hash']))
		queue.put([True, starLog['nonce']])
	else:
		app.logger.info('Not found after %s tries!' % (tries))

	return 'Found!' if found else 'Not found!'