#!/usr/bin/env python2
from imdbpie import Imdb
import mechanize
import logging
import sys
import subprocess
import tempfile
import os


def get_trakt_pin(url):
    """
    Get PIN provided by trakt.tv for exporting the movies in CSV format.

    :param str url: URL from which we fetch the PIN.
    :return Application PIN or None if operation was not successful
    :rtype str
    """

    assert isinstance(url, str)
    logger = logging.getLogger(__name__)

    # 2 Cases when we follow the link
    # - We are redirected to the page at which we fetch the PIN
    # - We are required to sign in first and then we get the PIN (as in first
    # case)

    not_signed_in_url = "https://trakt.tv/auth/signin"

    # kickstart mechanize.Browser instance
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.addheaders = [('User-agent', 'Firefox')]

    br.open(url)
    curr_url = br.geturl()

    if curr_url == not_signed_in_url:
        logger.warning("Not signed in trak.tv. Credentials are required.")

        res = submit_trakt_credentials(br)
        assert res

    # we are signed-in by now
    pin = br.geturl().split("/")[-1]
    logger.warning("Successfully signed in trakt.tv. PIN: {}".format(pin))

    return pin



def submit_trakt_credentials(mech_browser):
    """
    Fill the trakt.tv credentials

    :return True if operation was successful
    :rtype bool
    """

    # Get username and password
    # TODO: use pygpgme for doing this

    # Seems that I can't fetch the output of pass command..
    # write it to a temporary file and read of it.

    logger = logging.getLogger(__name__)

    trakt_user = "bergercookie"
    trakt_pass = None
    [f, fpath] = tempfile.mkstemp(text=True)
    res = subprocess.Popen(
        ["/usr/local/bin/pass", "trakt.tv/{u}".format(u=trakt_user)],
        stdout=f,
        stderr=subprocess.PIPE)
    res.communicate()

    os.lseek(f, 0, 0)
    trakt_pass = os.read(f, 100)
    trakt_pass = trakt_pass.rstrip(os.linesep)

    # remove file manually - not done by mkstemp call
    subprocess.check_call(["/usr/bin/srm", fpath])

    # form of interest is the 2nd
    prev_url = mech_browser.geturl()
    mech_browser.select_form(nr=1)
    mech_browser["user[login]"] = trakt_user
    mech_browser["user[password]"] = trakt_pass
    mech_browser.submit()

    assert trakt_pass

    if prev_url == mech_browser.geturl():
        logger.error("Couldn't get past authentication page!")
        return False
    else:
        return True



def main():
    """Main."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Initiating trakt => evernote syncing...")
    url = raw_input("Give me the url to search in: ")
    pin = get_trakt_pin(url)
    logger.warning("PIN: %s", pin)


if __name__ == "__main__":
    main()
