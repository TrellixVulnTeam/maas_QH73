package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"github.com/rs/zerolog"
	"github.com/spf13/cobra"

	"rackd/cmd/logger"
	"rackd/cmd/subcommands"
	"rackd/internal/metrics"
)

type opts struct {
	Euid     bool
	Version  bool
	NoDaemon bool
	NoSave   bool
	Syslog   bool
	GID      uint32
	UID      uint32
	Chroot   string
	RunDir   string
	LogFile  string
	LogLevel string
	Logger   string
	PIDFile  string
}

var (
	options opts
	Version string
)

var (
	rootCMD = &cobra.Command{
		Use:   "rackd",
		Short: "rack controller daemon",
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx, cancel := context.WithCancel(context.Background())
			if options.Version {
				printVersion()
				return nil
			}
			var (
				err error
				log zerolog.Logger
			)
			ctx, log, err = logger.New(ctx, options.Syslog, options.LogLevel, options.LogFile)
			if err != nil {
				return err
			}
			rootMetricsRegistry := metrics.NewRegistry("")
			metricsSrvr, err := metrics.NewPrometheus("127.0.0.1", 9090, nil, rootMetricsRegistry) // TODO make bind address configurable and provide TLS config
			if err != nil {
				return err
			}
			defer metricsSrvr.Close()
			log.Info().Msg("rackd started successfully")
			sigChan := make(chan os.Signal)
			signal.Notify(sigChan, syscall.SIGTERM, syscall.SIGINT)
			<-sigChan
			cancel()
			return nil
		},
	}
)

func init() {
	rootCMD.PersistentFlags().BoolVar(&options.Euid, "euid", false, "set only effective user-id rather than real user-id.")
	rootCMD.PersistentFlags().BoolVarP(&options.Version, "version", "v", false, "print version")
	rootCMD.PersistentFlags().BoolVar(&options.NoDaemon, "nodaemon", true, "don't daemonize, don't use default umask of 0077")
	rootCMD.PersistentFlags().BoolVar(&options.NoSave, "no_save", false, "do not save state on shutdow")
	rootCMD.PersistentFlags().BoolVar(&options.Syslog, "syslog", false, "log to syslog instead of file")
	rootCMD.PersistentFlags().Uint32Var(&options.GID, "gid", 0, "the gid to run as.  If not specified, the default gid associated with the specified --uid is used.")
	rootCMD.PersistentFlags().Uint32Var(&options.UID, "uid", 0, "the uid to run as")
	rootCMD.PersistentFlags().StringVar(&options.Chroot, "chroot", "", "chroot to a supplied directory before running")
	rootCMD.PersistentFlags().StringVar(&options.RunDir, "rundir", "", "change to a supplied directory before running")
	rootCMD.PersistentFlags().StringVar(&options.Logger, "logger", "json", "type of logger to use")
	rootCMD.PersistentFlags().StringVar(&options.LogFile, "log-file", "", "path to file to log to, stdout if not supplied")
	rootCMD.PersistentFlags().StringVar(&options.LogLevel, "log-level", "info", "log level (info|debug|warn|error)")
	rootCMD.PersistentFlags().StringVar(&options.PIDFile, "pid-file", "", "path to pid file when daemonized")
}

func printVersion() {
	fmt.Printf("version: %s\n", Version)
}

func main() {
	rootCMD.AddCommand(subcommands.RegisterCMD)
	rootCMD.AddCommand(subcommands.ConfigCMD)
	rootCMD.AddCommand(subcommands.ObserveCMD)
	rootCMD.AddCommand(subcommands.SendBeaconCMD)
	rootCMD.AddCommand(subcommands.ScanNetworkCMD)
	rootCMD.AddCommand(subcommands.SetupDNSCMD)
	rootCMD.AddCommand(subcommands.SupportDumpCMD)
	rootCMD.Execute()
}