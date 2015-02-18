#!/usr/bin/env python
"""Python daemonization lib
"""
from daemonize import Daemonize
import argparse
import sys
import os
import analysis.datafetch.twitter_fetch as tw
import logging
import logging.config
import json
import settings

LOG = logging.getLogger(__name__)

class Twitterd(object):
    """ Twitter Daemon Class
    """

    CMDS = ['stream_filter', 'search']
    NORTHANTS_BOX = '-1.386293,51.985165,-0.282167,52.650010'

    def __init__(self, args):
        self.init_args()
        self.args = self.get_args(args)
        #print(self.args)
        self.settings = self.read_settings(self.args.settings[0])
        self.init_logging(settings.LOGGING)
        self.fetcher = tw.create_datafetcher(self.settings["twitter"])

        self.cmd_map = {
            self.CMDS[0] : tw.DataFetcher.Cmd.stream_filter,
            self.CMDS[1] : tw.DataFetcher.Cmd.search,
        }

    def read_settings(self, settings_filename):
        settings_dict = {}
        with open(settings_filename, "r") as settings_file:
            settings_dict = json.load(settings_file)
        return settings_dict

    def init_logging(self, log_settings):
        logging.config.dictConfig(log_settings)

    def init_args(self):
        """ Initialize Arg parser
        """
        parser = argparse.ArgumentParser(description='Process some integers.')
        parser.add_argument('--outdir', metavar='OUTDIR', type=str, nargs=1,
                            required=True, help='Output Directory')
        parser.add_argument('--max-time', metavar='SECONDS', type=int, nargs='?',
                            required=False, help='Number of Seconds to run before termination')
        parser.add_argument('--cmd', metavar='CMD', choices=self.CMDS, type=str, nargs=1,
                            required=True, help='Command Name')
        parser.add_argument('--settings', metavar='SETTINGSFILE', type=str, nargs=1,
                            required=True, help='Command Name')
        self.parser = parser

    def get_args(self, args):
        """ Parse the arguments, and return a Namespace object
        """
        return self.parser.parse_args(args)
        
    def main(self):
        """ Main entry point for daemon
        """
        #pdb.set_trace()
        LOG.info("starting up...")
        try:
            self.download_data()
        except:
            LOG.exception("Unable to exec command")
        return
        
    def download_data(self):
        """ Run a twitter command and concatenate results to file
        """
        output_filename = os.path.join(self.args.outdir[0], "twitter_data.json")
        errors_filename = os.path.join(self.args.outdir[0], "twitter_errors.txt")

        max_time = self.args.max_time if (hasattr(self.args, "max_time")) else None

        kwargs = {}
        kwargs["locations"] = self.NORTHANTS_BOX
        if not max_time is None:
            kwargs["timeout"] = max_time
        kwargs["track"] = None
        kwargs["include_entities"] = 1
        

        out_file = open(output_filename, "w")
        
        err_file = open(errors_filename, "w")

        command = self.cmd_map[self.args.cmd[0]]

        try:
            status = self.fetcher.download_data(out_file,
                                                err_file,
                                                command=command,
                                                verbose=True,
                                                **kwargs)
            LOG.info("status=%d", status)
        finally:
            out_file.close()
            err_file.close()
        

def main():
    """ Read the command line args and start off the daemon
    """
    LOG.info("Started")
    program_name = sys.argv[0]
    daemon_cmd = sys.argv[1]
    handlers = LOG.handlers
    keep_fds = [handler.stream.fileno() for handler in handlers]

    if daemon_cmd == "start":
        twitterd = Twitterd(sys.argv[2:])
        def entry():
            twitterd.main()
        LOG.info("Daemonizing")
        """
        daemon = Daemonize(app=program_name,
                           pid="twitter_daemon.pid",
                           action=entry,
                           keep_fds=keep_fds)
        LOG.info("Daemonized")
        import pdb
        pdb.set_trace()
        daemon.start()
        LOG.error("Exiting")
        """
        entry()
    elif daemon_cmd == "stop":
        pass 
    elif daemon_cmd == "restart":
        pass

if __name__ == '__main__':
    main()
