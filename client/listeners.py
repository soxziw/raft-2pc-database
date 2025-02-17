import timeloop
import timedelta
import utils


prepare_reply_checker = timeloop.Timeloop()
    

"""Set up a new thread to periodically check the replies and request queue status for processing"""
@prepare_reply_checker.job(interval=timedelta(seconds=utils.JOB_INTERVAL))                          
def process_replies():
    pass