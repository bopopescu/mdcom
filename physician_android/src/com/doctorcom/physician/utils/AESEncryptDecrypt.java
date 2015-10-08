package com.doctorcom.physician.utils;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.OutputStream;
import java.security.Key;
import java.security.NoSuchAlgorithmException;
import java.security.spec.InvalidKeySpecException;

import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.PBEKeySpec;
import javax.crypto.spec.SecretKeySpec;

public class AESEncryptDecrypt {
	private SecretKeySpec skforAES = null;
	private IvParameterSpec IV;
	private final String CIPHERMODEPADDING = "AES/CBC/PKCS7Padding";
	public AESEncryptDecrypt(String secretKey, String secretKeyFile) {
		skforAES = initSecretKey(secretKey, secretKeyFile);
		// must save the IV for use when we want to decrypt the text
		byte[] iv = { 0xA, 1, 0xB, 5, 4, 0xF, 7, 9, 0x17, 3, 1, 6, 8, 0xC, 0xD, 91 };
		IV = new IvParameterSpec(iv);
	}
	
	private SecretKeySpec initSecretKey (String secretKey, String secretKeyFile) {
		SecretKeySpec skforAES = null;
		final String KEY_GENERATION_ALG = "PBEWITHSHA1AND128BITAES-CBC-BC";
		final int HASH_ITERATIONS = 10000;
		final int KEY_LENGTH = 256;
		char[] humanPassphrase = secretKey.toCharArray();
		byte[] salt = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF }; // must save this for next time we want the key
		PBEKeySpec myKeyspec = new PBEKeySpec(humanPassphrase, salt, HASH_ITERATIONS, KEY_LENGTH);
		SecretKeyFactory keyfactory = null;
		SecretKey sk = null;
		try {
			skforAES = (SecretKeySpec) readKey(secretKeyFile);
			if (skforAES == null) {
				keyfactory = SecretKeyFactory.getInstance(KEY_GENERATION_ALG);
				sk = keyfactory.generateSecret(myKeyspec);
				DocLog.d("AESEncryptDecrypt", "SecretKey generated");
				byte[] skAsByteArray = sk.getEncoded();
				skforAES = new SecretKeySpec(skAsByteArray, "AES");
				saveKey(skforAES, secretKeyFile);
			}
		} catch (NoSuchAlgorithmException nsae) {
			DocLog.d("AESEncryptDecrypt", "no key factory support for " + KEY_GENERATION_ALG, nsae);
		} catch (InvalidKeySpecException ikse) {
			DocLog.d("AESEncryptDecrypt", "invalid key spec for PBEWITHSHAANDTWOFISH-CBC", ikse);
		}
		return skforAES;
	}
	
	private static boolean saveKey(Key key, String secretKeyFile) {
		try {
			FileOutputStream fosKey = new FileOutputStream(secretKeyFile);
			ObjectOutputStream oos = new ObjectOutputStream(fosKey);
			oos.writeObject(key);
			oos.close();
			fosKey.close();
			return true;
		} catch (Exception e) {
			DocLog.e("AESEncryptDecrypt", "savekey", e);
			new File(secretKeyFile).delete();
			return false;
		}
	}

	private static Key readKey(String secretKeyFile) {
		if (secretKeyFile == null || secretKeyFile.equals("") || !new File(secretKeyFile).exists()) {
			return null;
		}
		Key key = null;
		try {
			FileInputStream fisKey = new FileInputStream(secretKeyFile);
			ObjectInputStream oisKey = new ObjectInputStream(fisKey);
			key = (Key) oisKey.readObject();
			oisKey.close();
			fisKey.close();
		} catch (Exception e) {
			DocLog.e("AESEncryptDecrypt", "readKey", e);
		}
		return key;
	}

	public String encrypt(String originalText) throws AESEncryptDecryptException {
		try {
			return toHex(encrypt(CIPHERMODEPADDING, skforAES, IV,
					originalText.getBytes("UTF-8")));
		} catch (Exception e) {
			throw new AESEncryptDecryptException(e);
		}
	}

	public void encrypt(File in, File out) throws AESEncryptDecryptException {
		try {
	        InputStream fis;
	        OutputStream fos;
			Cipher c = Cipher.getInstance(CIPHERMODEPADDING);
			c.init(Cipher.ENCRYPT_MODE, skforAES, IV);
			c.getOutputSize(100);
			fis = new BufferedInputStream(new FileInputStream(in));
			fos = new BufferedOutputStream(new FileOutputStream(out));
			int bufferLength = (in.length() > 1024 * 1024 ? 1024 * 1024 : 1024);
			byte[] buffer = new byte[bufferLength];
			int noBytes = 0;
			byte[] cipherBlock = new byte[c.getOutputSize(buffer.length)];
			int cipherBytes;			
	        while ((noBytes = fis.read(buffer)) != -1) {
	            cipherBytes = c.update(buffer, 0, noBytes, cipherBlock);
	            fos.write(cipherBlock, 0, cipherBytes);
	        }
	        // always call doFinal
	        cipherBytes = c.doFinal(cipherBlock, 0);
	        fos.write(cipherBlock, 0, cipherBytes);
	        // close the files
	        fos.flush();
	        fos.close();
	        fis.close();
		} catch (Exception e) {
			throw new AESEncryptDecryptException(e);
		}
	}
	
	byte[] encrypt(String cmp, SecretKey sk, IvParameterSpec IV, byte[] msg) throws AESEncryptDecryptException {
		try {
			Cipher c = Cipher.getInstance(cmp);
			c.init(Cipher.ENCRYPT_MODE, sk, IV);
			return c.doFinal(msg);
		} catch (Exception e) {
			throw new AESEncryptDecryptException(e);
		}
	}

	public String decrypt(String encryptingCode) throws AESEncryptDecryptException {
		try {
			return new String(decrypt(CIPHERMODEPADDING, skforAES, IV,
					toByte(encryptingCode)));
		} catch (Exception e) {
			throw new AESEncryptDecryptException(e);
		}
	}

	public void decrypt(File in, File out) throws AESEncryptDecryptException {
		try {
	        InputStream fis;
	        OutputStream fos;
			Cipher c = Cipher.getInstance(CIPHERMODEPADDING);
			c.init(Cipher.DECRYPT_MODE, skforAES, IV);
			fis = new BufferedInputStream(new FileInputStream(in));
			fos = new BufferedOutputStream(new FileOutputStream(out));
	
	        byte[] buffer = new byte[1024];
	        int noBytes = 0;
	        byte[] cipherBlock = new byte[c.getOutputSize(buffer.length)];
	        int cipherBytes;
	        while ((noBytes = fis.read(buffer)) != -1) {
	            cipherBytes = c.update(buffer, 0, noBytes, cipherBlock);
	            fos.write(cipherBlock, 0, cipherBytes);
	        }
	        // always call doFinal
	        cipherBytes = c.doFinal(cipherBlock, 0);
	        fos.write(cipherBlock, 0, cipherBytes);
	        // close the files
	        fos.flush();
	        fos.close();
	        fis.close();
		} catch (Exception e) {
			throw new AESEncryptDecryptException(e);
		}
	}
	
	byte[] decrypt(String cmp, SecretKey sk, IvParameterSpec IV,
			byte[] ciphertext) throws AESEncryptDecryptException {
		try {
			Cipher c = Cipher.getInstance(cmp);
			c.init(Cipher.DECRYPT_MODE, sk, IV);
			return c.doFinal(ciphertext);
		} catch (Exception e) {
			throw new AESEncryptDecryptException(e);
		}
	}

	public static byte[] toByte(String hexString) {
		int len = hexString.length() / 2;
		byte[] result = new byte[len];
		for (int i = 0; i < len; i++)
			result[i] = Integer.valueOf(hexString.substring(2 * i, 2 * i + 2),
					16).byteValue();
		return result;
	}

	public static String toHex(byte[] buf) {
		if (buf == null)
			return "";
		StringBuffer result = new StringBuffer(2 * buf.length);
		for (int i = 0; i < buf.length; i++) {
			appendHex(result, buf[i]);
		}
		return result.toString();
	}

	private final static String HEX = "0123456789ABCDEF";

	private static void appendHex(StringBuffer sb, byte b) {
		sb.append(HEX.charAt((b >> 4) & 0x0f)).append(HEX.charAt(b & 0x0f));
	}

	/**
	 * When encrypt or decrypt failed.
	 */
	public static class AESEncryptDecryptException extends Exception {

		private static final long serialVersionUID = -7313578707191110082L;
		public AESEncryptDecryptException() {
			super();
		}
		public AESEncryptDecryptException(String message) {
			super(message);
		}
		public AESEncryptDecryptException(Throwable t) {
			super(t);
		}
		public AESEncryptDecryptException(String message, Throwable t) {
			super(message, t);
		}
	}
}
