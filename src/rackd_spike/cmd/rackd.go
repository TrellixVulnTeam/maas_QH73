package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
	"github.com/spf13/cobra"

	"rackd/cmd/logger"
	"rackd/cmd/subcommands"
	"rackd/internal/config"
	"rackd/internal/dhcp"
	machinehelpers "rackd/internal/machine_helpers"
	"rackd/internal/metrics"
	"rackd/internal/service"
	"rackd/internal/transport"
	"rackd/pkg/authenticate"
	"rackd/pkg/controller"
	"rackd/pkg/region"
	"rackd/pkg/register"
)

type opts struct {
	Euid       bool
	Version    bool
	NoDaemon   bool
	NoSave     bool
	Syslog     bool
	GID        uint32
	UID        uint32
	Chroot     string
	RunDir     string
	LogFile    string
	LogLevel   string
	Logger     string
	PIDFile    string
	ConfigFile string
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
			defer cancel()
			if options.Version {
				printVersion()
				return nil
			}
			var (
				err error
				log *zerolog.Logger
			)

			ctx, log, err = logger.New(ctx, options.Syslog, options.LogFile)
			if err != nil {
				return err
			}

			ctx, err = config.Load(ctx, options.ConfigFile)
			if err != nil {
				return err
			}

			log, err = logger.SetLogLevel(log, options.LogLevel, config.Config.Debug)
			if err != nil {
				return err
			}

			// From here on, it's possible to gracefully stop the daemon
			ctx = cancelSignalContext(ctx)

			rootMetricsRegistry := metrics.NewRegistry("")
			metricTls, err := config.GetMetricsTlsConfig(ctx)
			if err != nil {
				return err
			}
			metricsSrvr, err := metrics.NewPrometheus(
				config.Config.Metrics.Bind,
				config.Config.Metrics.Port,
				metricTls,
				rootMetricsRegistry)
			if err != nil {
				return err
			}
			metricsSrvr.Start(ctx)

			sup := service.NewSupervisor()
			if config.Config.Proxy {
				sup.RegisterService(dhcp.NewRelaySvc())
			} else if machinehelpers.IsRunningInSnap() {
				dhcpv4, err := dhcp.NewDhcpdSupervisordService(config.SupervisordURL())
				if err != nil {
					return err
				}
				dhcpv6, err := dhcp.NewDhcpd6SupervisordService(config.SupervisordURL())
				if err != nil {
					return err
				}
				sup.RegisterService(dhcpv4)
				sup.RegisterService(dhcpv6)
			} else {
				dhcpv4, err := dhcp.NewDhcpdSystemdService(ctx)
				if err != nil {
					return err
				}
				dhcpv6, err := dhcp.NewDhcpd6SystemdService(ctx)
				if err != nil {
					return err
				}
				sup.RegisterService(dhcpv4)
				sup.RegisterService(dhcpv6)
			}

			rpcTls, err := config.GetRpcTlsConfig(ctx)
			if err != nil {
				return err
			}

			initRegion := config.Config.MaasUrl[0]
			rpcMgr := transport.NewRPCManager(rpcTls) // TODO use the register command to provide info
			rpcMgr.AddClient(ctx, authenticate.NewCapnpAuthenticator())
			rpcMgr.AddClient(ctx, register.NewCapnpRegisterer())
			rackController, err := controller.NewRackController(ctx, config.Config.Proxy, initRegion, sup)
			if err != nil {
				return err
			}
			rpcMgr.AddHandler(ctx, rackController)

			err = rpcMgr.Init(ctx, initRegion, func(ctx context.Context) error {
				return region.Handshake(ctx, initRegion, Version, rpcMgr)
			})
			if err != nil {
				return err
			}

			log.Info().Msgf("rackd %v started successfully", Version)

			sigChan := make(chan os.Signal, 2)
			signal.Notify(sigChan, syscall.SIGHUP, syscall.SIGUSR1)

			for {
				select {
				case <-ctx.Done():
					rpcMgr.Stop(context.Background())
					log.Info().Msg("rackd stopping")
					return nil

				case s := <-sigChan:
					switch s {
					case syscall.SIGHUP:
						err = config.Reload(ctx)
						log.Err(err).Msg("config reload")

						// Update debug level
						log, _ = logger.SetLogLevel(log, options.LogLevel, config.Config.Debug)

					case syscall.SIGUSR1:
						// reopen logfiles (logrotate)
						err = logger.ReOpen()
						log.Err(err).Msg("rotate logs")
					}
				}
			}
		},
	}
)

func cancelSignalContext(ctx context.Context) context.Context {
	ctx, cancel := context.WithCancel(ctx)

	go func() {
		chSig := make(chan os.Signal, 2)
		signal.Notify(chSig, syscall.SIGINT, syscall.SIGTERM)

		s := <-chSig
		log.Ctx(ctx).Info().Msgf("Catch signal %v, shutting down", s)
		cancel()
	}()

	return ctx
}

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
	rootCMD.PersistentFlags().StringVar(&options.ConfigFile, "config-file", "", "path to config file")
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
	err := rootCMD.Execute()
	if err != nil {
		os.Exit(1)
	}
}
