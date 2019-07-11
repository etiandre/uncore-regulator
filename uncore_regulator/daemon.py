import importlib
import signal
import time
import logging
import pylikwid


class Daemon():
    def _exit_handler(self, sig, frame):
        pylikwid.stop()
        logging.info("stop")
        pylikwid.finalize()
        if self._logfile: self._logfile.close()
        exit()

    def _logtofile(self, s):
        if self._logfile:
            self._logfile.write(s)
            self._logfile.write("\n")

    def set_logfile(self, logfile):
        self._logfile = open(logfile, 'w')

    def __init__(self, cores, logfile=None, regulator=None):
        if logfile:
            logging.info("Logging meters to {}".format(logfile))
            self._logfile = open(logfile, 'w')
        else:
            self._logfile = None
        if regulator:
            logging.info("Using regulator {}".format(regulator))
            r_module = importlib.import_module("."+regulator, package="uncore_regulator.regulators")
            self._regulator=getattr(r_module, regulator)()
        else:
            self._regulator = None
        logging.info("Reading cores {}".format(cores))
        self.cores = cores

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
        pylikwid.init(self.cores)
        print("initialized {} cores".format(
            pylikwid.getnumberofthreads()))
        self._gid = pylikwid.addeventset(estr)
        logging.info("added event set " + estr)
        pylikwid.setup(self._gid)
        signal.signal(signal.SIGINT, self._exit_handler)

    def run(self):
        self._logtofile(
            "t [s]\tMFLOP/s\tMEM bandwidth [MB/s]\tOperatoinal Intensity\tPower 0 [W]\tPower 1 [W]\tDRAM Pow. 0 [W]\tDRAM Pow. 1 [W]\tUncore freq. 0 [MHz]\tUncore freq. 1 [Mhz]"
        )
        for i in range(0, pylikwid.getnumberofevents(self._gid)):
            logging.info("event {}: {}".format(
                i, pylikwid.getnameofevent(self._gid, i)))
        logging.info("start metering")
        t = 0
        mes_interval = 2
        pylikwid.start()

        while True:
            time.sleep(mes_interval)
            pylikwid.read()
            tprime = pylikwid.gettimeofgroup(self._gid)
            dt = tprime - t
            t = tprime
            flop = 0
            datavolume = 0
            # Read PMCs on all self.cores of socket #0
            for core in range(0, 28, 2):
                PMC0 = pylikwid.getlastresult(self._gid, 0,
                                              self.cores.index(core))
                PMC1 = pylikwid.getlastresult(self._gid, 1,
                                              self.cores.index(core))
                PMC2 = pylikwid.getlastresult(self._gid, 2,
                                              self.cores.index(core))
                flop += (PMC0 * 2.0 + PMC1 + PMC2 * 4.0)
        # Read MBOXes only on socket #0 (socket 1 bug :( )
            MBOX0C0 = pylikwid.getlastresult(self._gid, 3, 0)
            MBOX0C1 = pylikwid.getlastresult(self._gid, 4, 0)
            MBOX1C0 = pylikwid.getlastresult(self._gid, 5, 0)
            MBOX1C1 = pylikwid.getlastresult(self._gid, 6, 0)
            MBOX2C0 = pylikwid.getlastresult(self._gid, 7, 0)
            MBOX2C1 = pylikwid.getlastresult(self._gid, 8, 0)
            MBOX3C0 = pylikwid.getlastresult(self._gid, 9, 0)
            MBOX3C1 = pylikwid.getlastresult(self._gid, 10, 0)
            MBOX4C0 = pylikwid.getlastresult(self._gid, 11, 0)
            MBOX4C1 = pylikwid.getlastresult(self._gid, 12, 0)
            MBOX5C0 = pylikwid.getlastresult(self._gid, 13, 0)
            MBOX5C1 = pylikwid.getlastresult(self._gid, 14, 0)
            MBOX6C0 = pylikwid.getlastresult(self._gid, 15, 0)
            MBOX6C1 = pylikwid.getlastresult(self._gid, 16, 0)
            MBOX7C0 = pylikwid.getlastresult(self._gid, 17, 0)
            MBOX7C1 = pylikwid.getlastresult(self._gid, 18, 0)
            # Read memory consumption on socket #0
            datavolume = (
                (MBOX0C0 + MBOX1C0 + MBOX2C0 + MBOX3C0 + MBOX4C0 + MBOX5C0 +
                 MBOX6C0 + MBOX7C0 + MBOX0C1 + MBOX1C1 + MBOX2C1 + MBOX3C1 +
                 MBOX4C1 + MBOX5C1 + MBOX6C1 + MBOX7C1) * 64.0)

            # read PWR and uncore freq on 0,1
            PWR0_0 = pylikwid.getlastresult(self._gid, 19, 0)
            PWR0_1 = pylikwid.getlastresult(self._gid, 19, 1)
            PWR3_0 = pylikwid.getlastresult(self._gid, 20, 0)
            PWR3_1 = pylikwid.getlastresult(self._gid, 20, 1)
            UNCORE_CLOCK_0 = pylikwid.getlastresult(self._gid, 21, 0)
            UNCORE_CLOCK_1 = pylikwid.getlastresult(self._gid, 21, 1)

            if datavolume != 0: oi = flop / datavolume
            else: oi = float('inf')

            power_0 = PWR0_0 / dt
            power_1 = PWR0_1 / dt
            dram_power_0 = PWR3_0 / dt
            dram_power_1 = PWR3_1 / dt
            uncore_freq_0 = UNCORE_CLOCK_0 / dt
            uncore_freq_1 = UNCORE_CLOCK_1 / dt

            if self._regulator:
                self._regulator.regulate(oi, flop / dt)

            self._logtofile("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                t, 1.0E-06 * flop / dt, 1.0E-06 * datavolume / dt, oi, power_0,
                power_1, dram_power_0, dram_power_1, 1.E-06 * uncore_freq_0,
                1.E-06 * uncore_freq_1))
