use std::fs::File;
use std::io::{Read, Write};
use std::os::unix::io::FromRawFd;

use anyhow::{anyhow, bail, Result};
use atty;

use crate::Config;

pub mod output {
	#[macro_export]
	/// Print Debug information if the option is set
	macro_rules! dprint {
		($args:expr $(,)?, $($arg: tt)*) => {
			if $args.debug() {
				let string = std::fmt::format(std::format_args!($($arg)*));
				eprintln!("DEBUG: {string}");
			}
		};
	}
	pub use dprint;
}
pub use output::dprint;

impl Config {
	pub fn debug(&self) -> bool { self.debug }

	pub fn verbose(&self) -> bool { self.verbose }

	/// Read from a file. if one isn't provided, stdin will be used.
	///
	/// Note, anything passed here will be explicitly read only.
	pub fn verify_input(&self) -> Result<Box<dyn Read>> {
		dprint!(self, "Verifying Input");
		if let Some(path) = &self.input {
			// dprint!()
			// If we're verifying the input, and the file doesn't exist
			// We need to send an error back
			if !path.exists() {
				// Implement asking if they'd like to create it.
				// And optionally what the file name should be
				bail!("Input File '{}' does not exist", path.display())
			}

			// Open the file for reading.
			dprint!(self, "Opening input file '{}'", path.display());
			let file = File::open(path)?;
			return Ok(Box::new(file));
		}
		// The path didn't work out, so we must be stdin.
		// If stdin is attached to a tty, then it's not piped
		// This is considered no input as it won't work
		if atty::is(atty::Stream::Stdin) {
			bail!("No Input could be detected.")
		}
		// We have to use unsafe here because we can't have a buffer.
		// We Manage the buffer ourselves as the tag will be
		// 16 extra bytes than the input
		Ok(Box::new(unsafe { File::from_raw_fd(0) }))
		// Ok(Box::new(std::io::stdin().lock()))
	}

	pub fn verify_output(&self) -> Result<Box<dyn Write>> {
		dprint!(self, "Verifying Output");
		if let Some(path) = &self.output {
			if path.is_dir() {
				return Err(anyhow!("Path '{}' is a directory", path.display()).context(
					"Recursive encryptions are not yet supported\n       Consider making an \
					 archive with 'tar' and piping to binlock",
				));
			}

			// The file does not exist, we will create it.
			dprint!(self, "Creating file '{}'", path.display());
			let file = File::create(path)?;
			return Ok(Box::new(file));
		}
		// the path didn't work out, so we must be stdout.
		dprint!(self, "No output requested, using stdout");
		// We have to use unsafe here because we can't have a buffer.
		// We Manage the buffer ourselves as the tag will be
		// 16 extra bytes than the input
		Ok(Box::new(unsafe { File::from_raw_fd(1) }))
		// Ok(Box::new(std::io::stdout().lock()))
	}
}
