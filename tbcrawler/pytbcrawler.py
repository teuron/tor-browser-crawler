import argparse
import sys
import traceback
from logging import INFO, DEBUG
from os import stat
from os.path import isfile, join
from shutil import copyfile
from sys import maxsize, argv

from tbselenium.tbdriver import TorBrowserDriver

import tbcrawler.common as cm
from tbcrawler import utils as ut
from tbcrawler.crawler import CrawlerBase
from tbcrawler.log import wl_log, add_symlink


def run():
    # build dirs
    build_crawl_dirs()

    # Parse arguments
    args = parse_arguments()

    # Read URLs
    url_list = read_list_urls(args.url_file, args.start, args.stop)

    # Add exceptions for all urls:
    for url in url_list:
        TorBrowserDriver.add_exception(url)

    # Instantiate crawler
    crawler = CrawlerBase(cm.CRAWL_DIR, cm.TORRC,
                          args.virtual_display, args.capture_screen)

    # Run the crawl
    try:
        crawler.crawl(url_list, args.batches, args.instances)
    except KeyboardInterrupt:
        wl_log.warning("Keyboard interrupt! Quitting...")
        sys.exit(-1)


def build_crawl_dirs():
    # build crawl directory
    ut.create_dir(cm.CRAWL_DIR)
    ut.create_dir(cm.LOGS_DIR)
    copyfile(cm.TORRC_FILE, join(cm.LOGS_DIR, 'torrc'))
    copyfile(cm.FFPREF_FILE, join(cm.LOGS_DIR, 'ffprefs'))
    add_symlink(join(cm.RESULTS_DIR, 'latest_crawl'), cm.CRAWL_DIR)


def read_list_urls(file_path, start, stop):
    """Return list of urls from a file."""
    assert (isfile(file_path))  # check that file exists
    assert (not stat(file_path).st_size == 0)  # check that file is not empty
    url_list = []
    try:
        with open(file_path) as f:
            file_contents = f.read()
            url_list = file_contents.splitlines()
            url_list = url_list[start - 1:stop]
    except Exception as e:
        ut.die("ERROR: while parsing URL list: {} \n{}".format(e, traceback.format_exc()))
    return url_list


def parse_arguments():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Crawl a list of URLs in multiple batches.')

    # List of urls to be crawled
    parser.add_argument('-u', '--url-file', required=True,
                        help='Path to the file that contains the list of URLs to crawl.')
    parser.add_argument('-o', '--output',
                        help='Directory to dump the results (default=./results).',
                        default=cm.CRAWL_DIR)
    parser.add_argument('-b', '--tbb-path',
                        help="Path to the Tor Browser Bundle directory.",
                        default=cm.TBB_DEFAULT_DIR)
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='increase output verbosity',
                        default=False)

    # For understanding batch and instance parameters please refer
    # to Wang and Goldberg's WPES'13 paper, Section 4.1.4
    parser.add_argument('--batches', type=int,
                        help='Number of batches in the crawl (default: %s)' % cm.NUM_BATCHES,
                        default=cm.NUM_BATCHES)
    parser.add_argument('--instances', type=int,
                        help='Number of instances to crawl for each web page (default: %s)' % cm.NUM_INSTANCES,
                        default=cm.NUM_INSTANCES)
    # Crawler features
    parser.add_argument('-x', '--virtual-display', action='store_true',
                        help='Use a virtual display (for headless browsing)',
                        default=False)
    parser.add_argument('-c', '--capture-screen', action='store_true',
                        help='Capture page screenshots',
                        default=False)

    # Limit crawl
    parser.add_argument('--start', type=int,
                        help='Select URLs from this line number: (default: 1).',
                        default=1)
    parser.add_argument('--stop', type=int,
                        help='Select URLs after this line number: (default: EOF).',
                        default=maxsize)

    # Parse arguments
    args = parser.parse_args()

    # Set verbose level
    wl_log.setLevel(DEBUG if args.verbose else INFO)
    del args.verbose

    # Change results dir if output
    cm.CRAWL_DIR = args.output
    del args.output

    wl_log.debug("Command line parameters: %s" % argv)
    return args


if __name__ == '__main__':
    run()