use std::collections::HashMap;
use std::io::Read;

use aes_gcm::{
	aead::{Aead, KeyInit, Payload},
	Aes256Gcm,
	Nonce, // Or `Aes128Gcm`
};
use anyhow::{anyhow, bail, Context, Result};
use rand::rngs::StdRng;
use rand::{RngCore, SeedableRng};
use rpassword::prompt_password;
use serde::{Deserialize, Serialize};
use {argon2, hex, serde_json};

pub fn get_password(decrypt: bool) -> Result<(String)> {
	loop {
		let password = prompt_password("Password: ")?;
		if decrypt {
			return Ok(password);
		}

		if password == prompt_password("Confirm Password: ")? {
			return Ok(password);
		}
		drop(password);
		eprintln!("Passwords don't match! Try again.")
	}
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Header {
	binlock: String,
	salt: String,
	iv: String,
	aad: String,
}

#[derive(Debug)]
pub struct Crypto {
	data: HashMap<&'static str, Vec<u8>>,
}

impl Crypto {
	pub fn new() -> Crypto {
		// define keys, and buffer length
		let keys = [("salt", 32), ("iv", 12), ("aad", 16)];

		let mut data = HashMap::new();
		// Fill the buffers and add to HashMap
		// Use new entropy for each buffer
		for (key, value) in keys {
			let mut buffer = [0; 32];
			let mut rng = StdRng::from_entropy();
			rng.fill_bytes(&mut buffer);

			data.insert(key, buffer[0..value].to_vec());
		}
		Crypto { data }
	}

	pub fn create_key(&mut self, password: &[u8]) -> Result<()> {
		self.data.insert(
			"key",
			argon2::hash_raw(password, self.get("salt")?, &argon2::Config::default())?,
		);
		Ok(())
	}

	pub fn hex_header(&self) -> Result<Header> {
		let context = "Could not create header";
		Ok(Header {
			binlock: "0.3.0".to_string(),
			salt: hex::encode(self.get("salt").context(context)?),
			iv: hex::encode(self.get("iv").context(context)?),
			aad: hex::encode(self.get("aad").context(context)?),
		})
	}

	pub fn create_header(&self) -> Result<Vec<u8>> {
		let mut header = serde_json::to_vec(&self.hex_header()?)?;

		if header.len() < 512 {
			let padding = 512 - header.len();
			for _ in 0..padding {
				header.push(0)
			}
		}
		Ok(header)
	}

	pub fn read_header(&self, input: &mut Box<dyn Read>) -> Result<Header> {
		// Read the first 512 of input
		let mut buffer = [0; 512];
		input.read_exact(&mut buffer)?;

		// Remove Null byte padding
		let mut header = Vec::new();
		for byte in buffer {
			if byte != 0 {
				header.push(byte);
			}
		}
		// Serialize the json string into Header
		serde_json::from_slice(&header).context("File does not appear to be a Binlock file")
	}

	pub fn load_header(&mut self, header: &Header) -> Result<()> {
		self.data.insert("salt", hex::decode(&header.salt)?);
		self.data.insert("iv", hex::decode(&header.iv)?);
		self.data.insert("aad", hex::decode(&header.aad)?);
		Ok(())
	}

	pub fn get(&self, key: &str) -> Result<&Vec<u8>> {
		self.data
			.get(key)
			.ok_or_else(|| anyhow!("{key} Does not exist"))
	}

	pub fn encrypt(&self, buffer: &mut [u8]) -> Result<Vec<u8>> {
		// Setup the cipher
		let context = "Could not encrypt";
		let key = self.get("key").context(context)?;
		let iv = self.get("iv").context(context)?;
		let aad = self.get("aad").context(context)?;

		let cipher = match Aes256Gcm::new_from_slice(key) {
			Ok(aes) => aes,
			Err(_) => bail!("Invalid length during encryption"),
		};
		// eprintln!("{}", buffer.len());
		match cipher.encrypt(Nonce::from_slice(iv), Payload { msg: buffer, aad }) {
			Ok(vec) => Ok(vec),
			// Encryption error doesn't work with anyhow.
			// It returns no useful message due to security constraints
			Err(_) => bail!("Encryption Failed"),
		}
	}

	pub fn decrypt(&self, buffer: &mut [u8]) -> Result<Vec<u8>> {
		let context = "Could not decrypt";
		let key = self.get("key").context(context)?;
		let iv = self.get("iv").context(context)?;
		let aad = self.get("aad").context(context)?;

		let cipher = match Aes256Gcm::new_from_slice(key) {
			Ok(aes) => aes,
			Err(_) => bail!("Invalid length during decryption"),
		};
		// eprintln!("{}", buffer.len());
		match cipher.decrypt(Nonce::from_slice(iv), Payload { msg: buffer, aad }) {
			Ok(vec) => Ok(vec),
			// Decryption error doesn't work with anyhow.
			// It returns no useful message due to security constraints
			Err(_) => bail!("Decryption Failed"),
		}
	}
}
