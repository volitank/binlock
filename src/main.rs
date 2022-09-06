// Clap Parser needs to be in scope
use std::io::{Read, Write};

use anyhow::Result;
use clap::Parser;
use cli::Config;

mod cli;
mod config;
mod crypto;
use crate::cli::{BinlockArgs, Commands};
use crate::crypto::{get_password, Crypto};

fn main() -> Result<()> {
	let args = BinlockArgs::parse();
	if args.debug {
		for line in format!("{args:#?}").lines() {
			eprintln!("DEBUG: {line}");
		}
	}

	match args.command {
		Commands::Encrypt(encrypt) => encryptor(encrypt)?,
		Commands::Decrypt(decrypt) => decryptor(decrypt)?,
	}
	Ok(())
}

fn encryptor(config: Config) -> Result<()> {
	let mut input = config.verify_input()?;
	let mut output = config.verify_output()?;

	let mut crypto = Crypto::new();
	crypto.create_key(get_password(false)?.as_bytes())?;

	// Write our header before anything else is done
	output.write_all(&crypto.create_header()?)?;

	loop {
		// Buffer is 128Kb
		// let mut bytes = [0; 131072];
		// Buffer is 60KiB - 16 bytes for the tag
		let mut bytes = [0; 61424];

		let amount_read = input.read(&mut bytes)?;
		if amount_read == 0 {
			break;
		}
		output.write_all(&crypto.encrypt(&mut bytes[0..amount_read])?)?;

		output.flush()?;
	}

	Ok(())
}

fn decryptor(config: Config) -> Result<()> {
	let mut input = config.verify_input()?;
	let mut output = config.verify_output()?;

	let mut crypto = Crypto::new();

	let header = crypto.read_header(&mut input)?;
	crypto.load_header(&header)?;
	crypto.create_key(get_password(true)?.as_bytes())?;

	loop {
		// Buffer is 128Kb + tag size 16 bytes
		// let mut bytes = [0; 131088];
		// Buffer is 60KiB
		let mut bytes = [0; 61440];

		let amount_read = input.read(&mut bytes)?;
		if amount_read == 0 {
			break;
		}

		output.write_all(&crypto.decrypt(&mut bytes[0..amount_read])?)?;

		output.flush()?;
	}

	Ok(())
}
