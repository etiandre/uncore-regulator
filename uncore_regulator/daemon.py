import importlib
import signal
import time
import logging
import pylikwid
import threading


class Daemon(threading.Thread):
    def __init__(self, cores, sockets, sleep_dt, outfile=None, regulator=None):
        threading.Thread.__init__(self)
        self.stop = threading.Event()
        self._regulator = None
        if outfile:
            logging.info("Logging meters to {}".format(outfile))
            self._outfile = open(outfile, 'w')
        else:
            logging.info("Not logging anything")
            self._outfile = None
        logging.info("Using cores {} and sockets {}".format(cores, sockets))
        self.cores = cores
        self.sockets = sockets
        self.measured_cores = list(set.union(cores, sockets))
        logging.info("-> Metering on {}".format(self.measured_cores))
        self.sleep_dt = sleep_dt
        logging.info("Measuring every {} seconds".format(self.sleep_dt))
        # https://github.com/RRZE-HPC/likwid/blob/master/groups/broadwellEP/MEM_DP.txt
        estr = "FP_ARITH_INST_RETIRED_128B_PACKED_DOUBLE:PMC0,"
        estr += "FP_ARITH_INST_RETIRED_SCALAR_DOUBLE:PMC1,"
        estr += "FP_ARITH_INST_RETIRED_256B_PACKED_DOUBLE:PMC2,"
        estr += "CAS_COUNT_RD:MBOX0C0,"
        estr += "CAS_COUNT_WR:MBOX0C1,"
        estr += "CAS_COUNT_RD:MBOX1C0,"
        estr += "CAS_COUNT_WR:MBOX1C1,"
        estr += "CAS_COUNT_RD:MBOX2C0,"
        estr += "CAS_COUNT_WR:MBOX2C1,"
        estr += "CAS_COUNT_RD:MBOX3C0,"
        estr += "CAS_COUNT_WR:MBOX3C1,"
        estr += "CAS_COUNT_RD:MBOX4C0,"
        estr += "CAS_COUNT_WR:MBOX4C1,"
        estr += "CAS_COUNT_RD:MBOX5C0,"
        estr += "CAS_COUNT_WR:MBOX5C1,"
        estr += "CAS_COUNT_RD:MBOX6C0,"
        estr += "CAS_COUNT_WR:MBOX6C1,"
        estr += "CAS_COUNT_RD:MBOX7C0,"
        estr += "CAS_COUNT_WR:MBOX7C1,"
        estr += "PWR_PKG_ENERGY:PWR0,"
        estr += "PWR_DRAM_ENERGY:PWR3,"
        estr += "UNCORE_CLOCK:UBOXFIX"
        pylikwid.init(self.measured_cores)
        logging.info("initialized {} threads".format(
            pylikwid.getnumberofthreads()))
        self._gid = pylikwid.addeventset(estr)
        pylikwid.setup(self._gid)

    def _logtofile(self, s):
        if self._outfile:
            self._outfile.write(s)
            self._outfile.write("\n")

    def set_outfile(self, outfile):
        self._outfile = open(outfile, 'w')

    def set_regulator(self, regulator):
        self._regulator = regulator

    def run(self):
        self._logtofile(
            "t [s]\tMFLOP/s\tMEM bandwidth [MB/s]\tOperational Intensity\t" +
            "\t".join(
                "Power {0} [W]\tDRAM Pow. {0} [W]\tUncore freq. {0} [MHz]".
                format(i) for i in self.sockets))
        for i in range(0, pylikwid.getnumberofevents(self._gid)):
            logging.info("event {}: {}".format(
                i, pylikwid.getnameofevent(self._gid, i)))
        logging.info("Start metering!")
        t = 0
        pylikwid.start()

        while True:
            if self.stop.wait(timeout=self.sleep_dt):
                pylikwid.stop()
                logging.info("Stopped metering")
                pylikwid.finalize()
                if self._outfile: self._outfile.close()
                break
            pylikwid.read()
            tprime = pylikwid.gettimeofgroup(self._gid)
            d = {}
            dt = tprime - t
            t = tprime
            d["t"] = t
            d["dt"] = dt
            # Read PMCs on all cores
            flop = 0
            for core in self.cores:
                PMC0 = pylikwid.getlastresult(self._gid, 0,
                                              self.measured_cores.index(core))
                PMC1 = pylikwid.getlastresult(self._gid, 1,
                                              self.measured_cores.index(core))
                PMC2 = pylikwid.getlastresult(self._gid, 2,
                                              self.measured_cores.index(core))
                flop += (PMC0 * 2.0 + PMC1 + PMC2 * 4.0)
            d["flop/s"] = flop / dt

            # Read sockets
            datavolume = 0
            for socket in self.sockets:
                MBOX0C0 = pylikwid.getlastresult(
                    self._gid, 3, self.measured_cores.index(socket))
                MBOX0C1 = pylikwid.getlastresult(
                    self._gid, 4, self.measured_cores.index(socket))
                MBOX1C0 = pylikwid.getlastresult(
                    self._gid, 5, self.measured_cores.index(socket))
                MBOX1C1 = pylikwid.getlastresult(
                    self._gid, 6, self.measured_cores.index(socket))
                MBOX2C0 = pylikwid.getlastresult(
                    self._gid, 7, self.measured_cores.index(socket))
                MBOX2C1 = pylikwid.getlastresult(
                    self._gid, 8, self.measured_cores.index(socket))
                MBOX3C0 = pylikwid.getlastresult(
                    self._gid, 9, self.measured_cores.index(socket))
                MBOX3C1 = pylikwid.getlastresult(
                    self._gid, 10, self.measured_cores.index(socket))
                MBOX4C0 = pylikwid.getlastresult(
                    self._gid, 11, self.measured_cores.index(socket))
                MBOX4C1 = pylikwid.getlastresult(
                    self._gid, 12, self.measured_cores.index(socket))
                MBOX5C0 = pylikwid.getlastresult(
                    self._gid, 13, self.measured_cores.index(socket))
                MBOX5C1 = pylikwid.getlastresult(
                    self._gid, 14, self.measured_cores.index(socket))
                MBOX6C0 = pylikwid.getlastresult(
                    self._gid, 15, self.measured_cores.index(socket))
                MBOX6C1 = pylikwid.getlastresult(
                    self._gid, 16, self.measured_cores.index(socket))
                MBOX7C0 = pylikwid.getlastresult(
                    self._gid, 17, self.measured_cores.index(socket))
                MBOX7C1 = pylikwid.getlastresult(
                    self._gid, 18, self.measured_cores.index(socket))
                datavolume += ((MBOX0C0 + MBOX1C0 + MBOX2C0 + MBOX3C0 +
                                MBOX4C0 + MBOX5C0 + MBOX6C0 + MBOX7C0 +
                                MBOX0C1 + MBOX1C1 + MBOX2C1 + MBOX3C1 +
                                MBOX4C1 + MBOX5C1 + MBOX6C1 + MBOX7C1) * 64.0)
                # read PWR and uncore freq on sockets
                PWR0 = pylikwid.getlastresult(
                    self._gid, 19, self.measured_cores.index(socket))
                d["pkg-power_" + str(socket)] = PWR0 / d["dt"]
                PWR3 = pylikwid.getlastresult(
                    self._gid, 20, self.measured_cores.index(socket))
                d["dram-power_" + str(socket)] = PWR3 / d["dt"]
                UNCORE_CLOCK = pylikwid.getlastresult(self._gid, 21, 0)
                d["uncore-freq_" + str(socket)] = UNCORE_CLOCK / d["dt"]

            d["memory-bandwidth"] = datavolume / dt
            if datavolume != 0: d["operational-intensity"] = flop / datavolume
            else: d["operational-intensity"] = float('inf')

            if self._regulator:
                self._regulator.regulate(d)

            self._logtofile("\t".join(
                str(i) for i in [
                    d["t"], 1.0E-06 * d["flop/s"], 1.0E-06 *
                    d["memory-bandwidth"], d["operational-intensity"],
                    "\t".join(
                        str(d["pkg-power_" + str(s)]) + "\t" +
                        str(d["dram-power_" + str(s)]) + "\t" +
                        str(1.E-06 * d["uncore-freq_" + str(s)])
                        for s in self.sockets)
                ]))
