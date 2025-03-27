import common.utils
def safe_store_bets(bets, file_lock):
    file_lock.acquire()
    try:
        common.utils.store_bets(bets)
    finally:
        file_lock.release()