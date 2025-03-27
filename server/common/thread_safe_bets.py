import common.utils
def safe_store_bets(bets, file_lock):
    file_lock.acquire()
    try:
        common.utils.store_bets(bets)
    finally:
        file_lock.release()

def safe_load_bets(file_lock) -> list[common.utils.Bet]:
    file_lock.acquire()
    try:
        ret = common.utils.load_bets()
    finally:
        file_lock.release()
        return ret
