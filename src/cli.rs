use std::path::PathBuf;

use clap::{Args, Parser, Subcommand};

#[derive(Parser, Debug)]
#[clap(name = "binlock")]
#[clap(author = "Blake Lee <blake@volian.org>")]
#[clap(version = "0.2.0")]
#[clap(about = "Does awesome things", long_about = None)]
pub struct BinlockArgs {
	// #[clap(short, long, value_parser, value_name = "FILE")]
	// pub input: Option<PathBuf>,

	// #[clap(short, long, value_parser, value_name = "FILE")]
	// pub output: Option<PathBuf>,
	#[clap(global = true, short, long, action)]
	pub verbose: bool,

	#[clap(global = true, short, long, action)]
	pub debug: bool,

	#[clap(subcommand)]
	pub command: Commands,
}

#[derive(Subcommand, Debug)]
pub enum Commands {
	Encrypt(Config),
	Decrypt(Config),
}

#[derive(Args, Debug)]
pub struct Config {
	#[clap(short, long, value_parser, value_name = "FILE")]
	pub input: Option<PathBuf>,

	#[clap(short, long, value_parser, value_name = "FILE")]
	pub output: Option<PathBuf>,

	#[clap(global = true, short, long, action)]
	pub verbose: bool,

	#[clap(global = true, short, long, action)]
	pub debug: bool,
}
