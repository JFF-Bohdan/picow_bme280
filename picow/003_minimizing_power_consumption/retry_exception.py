import functools
import math
import time



def retry_exception(attempts=5, delay_seconds=5, backoff_factor=2, exceptions=None):  # noqa
    """
    This is decorator designed to be used on a function or method that throws
    an exception when it fails

    :param attempts: the number of attempts you want to make
    :param delay_seconds: beginning amount of time you want to wait between attempts
    :param backoff_factor: the multiplicative factor you want to apply to your current dela after each wait
    :param exceptions: a list of exceptions you want to catch
    """

    if exceptions is None:
        exceptions = [BaseException]

    if backoff_factor < 1:
        raise ValueError("The backoff_factor factor must be greater or equal to 1")

    attempts = math.floor(attempts)
    if attempts < 0:
        raise ValueError("The number of attempts must be 0 or greater")

    if delay_seconds <= 0:
        raise ValueError("The delay_seconds must be greater than 0")

    def decorator_retry(function):
        @functools.wraps(function)
        def function_with_retries(*args, **kwargs):
            retry_attempts, retry_delay = attempts, delay_seconds

            while retry_attempts > 0:
                try:
                    return function(*args, **kwargs)

                # this is frowned upin, but I think justified in this case as we're checking against specific
                # exception types on the next line
                except BaseException as e:
                    print(f"Exception when retrying: {e}")
                    catch = any([isinstance(e, exctype) for exctype in exceptions])
                    if not catch:
                        raise

                    retry_attempts -= 1
                    if retry_attempts > 0:
                        time.sleep(retry_delay)
                        retry_delay *= backoff_factor
                    else:
                        raise

        function_with_retries._original = function
        return function_with_retries

    return decorator_retry

