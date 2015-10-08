-- MySQL dump 10.13  Distrib 5.1.59, for apple-darwin10.8.0 (i386)
--
-- Host: localhost    Database: clean_db
-- ------------------------------------------------------
-- Server version	5.1.59

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `Billing_billingaccount`
--

DROP TABLE IF EXISTS `Billing_billingaccount`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Billing_billingaccount` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `last_billing_success` datetime DEFAULT NULL,
  `last_billed_failure` datetime DEFAULT NULL,
  `status` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `address1` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `address2` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `city` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `state` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `nation` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `zip` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `cc_type` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `cc_num` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `cc_exp_month` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `cc_exp_year` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `identity_verifier` int(11) DEFAULT NULL,
  `last_modified` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Billing_billingaccount_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Billing_billingaccount`
--

LOCK TABLES `Billing_billingaccount` WRITE;
/*!40000 ALTER TABLE `Billing_billingaccount` DISABLE KEYS */;
/*!40000 ALTER TABLE `Billing_billingaccount` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Billing_billingfundsbucket`
--

DROP TABLE IF EXISTS `Billing_billingfundsbucket`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Billing_billingfundsbucket` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `account_id` int(11) NOT NULL,
  `balance` decimal(10,2) NOT NULL,
  `refill_trigger` decimal(8,2) NOT NULL,
  `refill_bucket_size` decimal(6,2) NOT NULL,
  `auto_refill_on` tinyint(1) NOT NULL,
  `last_modified` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Billing_billingfundsbucket_account_id` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Billing_billingfundsbucket`
--

LOCK TABLES `Billing_billingfundsbucket` WRITE;
/*!40000 ALTER TABLE `Billing_billingfundsbucket` DISABLE KEYS */;
/*!40000 ALTER TABLE `Billing_billingfundsbucket` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Billing_billingtransaction`
--

DROP TABLE IF EXISTS `Billing_billingtransaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Billing_billingtransaction` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `account_id` int(11) NOT NULL,
  `gateway` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `gateway_login` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `amount` decimal(7,2) NOT NULL,
  `sale_id` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `sale_date` datetime NOT NULL,
  `product_description` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `charge_was_a_debit` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Billing_billingtransaction_account_id` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Billing_billingtransaction`
--

LOCK TABLES `Billing_billingtransaction` WRITE;
/*!40000 ALTER TABLE `Billing_billingtransaction` DISABLE KEYS */;
/*!40000 ALTER TABLE `Billing_billingtransaction` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Billing_minutesproduct`
--

DROP TABLE IF EXISTS `Billing_minutesproduct`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Billing_minutesproduct` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `account_id` int(11) NOT NULL,
  `current_price_per_50_minutes` decimal(5,2) NOT NULL,
  `last_modified` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Billing_minutesproduct_account_id` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Billing_minutesproduct`
--

LOCK TABLES `Billing_minutesproduct` WRITE;
/*!40000 ALTER TABLE `Billing_minutesproduct` DISABLE KEYS */;
/*!40000 ALTER TABLE `Billing_minutesproduct` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `DoctorCom_click2call_log`
--

DROP TABLE IF EXISTS `DoctorCom_click2call_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DoctorCom_click2call_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `callid` varchar(34) COLLATE utf8_unicode_ci NOT NULL,
  `caller_id` int(11) NOT NULL,
  `called_user_id` int(11) DEFAULT NULL,
  `called_number` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `current_site_id` int(11) DEFAULT NULL,
  `timestamp` datetime NOT NULL,
  `source` varchar(3) COLLATE utf8_unicode_ci NOT NULL DEFAULT 'WEB',
  `caller_number` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `connected` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `DoctorCom_click2call_log_caller_id` (`caller_id`),
  KEY `DoctorCom_click2call_log_called_id` (`called_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DoctorCom_click2call_log`
--

LOCK TABLES `DoctorCom_click2call_log` WRITE;
/*!40000 ALTER TABLE `DoctorCom_click2call_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `DoctorCom_click2call_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `DoctorCom_click2call_session`
--

DROP TABLE IF EXISTS `DoctorCom_click2call_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DoctorCom_click2call_session` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `callid` varchar(34) COLLATE utf8_unicode_ci NOT NULL,
  `caller_id` int(11) NOT NULL,
  `called_user_id` int(11) DEFAULT NULL,
  `called_number` varchar(12) COLLATE utf8_unicode_ci NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `DoctorCom_click2call_session_caller_id` (`caller_id`),
  KEY `DoctorCom_click2call_session_called_id` (`called_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DoctorCom_click2call_session`
--

LOCK TABLES `DoctorCom_click2call_session` WRITE;
/*!40000 ALTER TABLE `DoctorCom_click2call_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `DoctorCom_click2call_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `DoctorCom_message`
--

DROP TABLE IF EXISTS `DoctorCom_message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DoctorCom_message` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sender_id` int(11) NOT NULL,
  `body` longtext COLLATE utf8_unicode_ci NOT NULL,
  `timestamp` datetime NOT NULL,
  `reply_id` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `DoctorCom_message_sender_id` (`sender_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DoctorCom_message`
--

LOCK TABLES `DoctorCom_message` WRITE;
/*!40000 ALTER TABLE `DoctorCom_message` DISABLE KEYS */;
/*!40000 ALTER TABLE `DoctorCom_message` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `DoctorCom_message_user_recipients`
--

DROP TABLE IF EXISTS `DoctorCom_message_user_recipients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DoctorCom_message_user_recipients` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `message_id` int(11) NOT NULL,
  `mhluser_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `message_id` (`message_id`,`mhluser_id`),
  KEY `mhluser_id_refs_user_ptr_id_4969198a81a86c57` (`mhluser_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DoctorCom_message_user_recipients`
--

LOCK TABLES `DoctorCom_message_user_recipients` WRITE;
/*!40000 ALTER TABLE `DoctorCom_message_user_recipients` DISABLE KEYS */;
/*!40000 ALTER TABLE `DoctorCom_message_user_recipients` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `DoctorCom_messagelog`
--

DROP TABLE IF EXISTS `DoctorCom_messagelog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DoctorCom_messagelog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `message_id` int(11) NOT NULL,
  `message_recipient_id` int(11) NOT NULL,
  `success` tinyint(1) NOT NULL,
  `confirmation` varchar(250) COLLATE utf8_unicode_ci NOT NULL,
  `twilio_sid` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `twilio_status` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `body_fragment` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `resend_of_id` int(11) DEFAULT NULL,
  `current_site_id` int(11) DEFAULT NULL,
  `tx_number` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `rx_number` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `tx_name` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `rx_name` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `DoctorCom_messagelog_message_id` (`message_id`),
  KEY `DoctorCom_messagelog_message_recipient_id` (`message_recipient_id`),
  KEY `DoctorCom_messagelog_twilio_sid` (`twilio_sid`),
  KEY `DoctorCom_messagelog_resend_of_id` (`resend_of_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DoctorCom_messagelog`
--

LOCK TABLES `DoctorCom_messagelog` WRITE;
/*!40000 ALTER TABLE `DoctorCom_messagelog` DISABLE KEYS */;
/*!40000 ALTER TABLE `DoctorCom_messagelog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `DoctorCom_messagetemp`
--

DROP TABLE IF EXISTS `DoctorCom_messagetemp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DoctorCom_messagetemp` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `body` varchar(140) COLLATE utf8_unicode_ci NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `DoctorCom_messagetemp_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DoctorCom_messagetemp`
--

LOCK TABLES `DoctorCom_messagetemp` WRITE;
/*!40000 ALTER TABLE `DoctorCom_messagetemp` DISABLE KEYS */;
/*!40000 ALTER TABLE `DoctorCom_messagetemp` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `DoctorCom_messagetemp_user_recipients`
--

DROP TABLE IF EXISTS `DoctorCom_messagetemp_user_recipients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DoctorCom_messagetemp_user_recipients` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `messagetemp_id` int(11) NOT NULL,
  `mhluser_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `messagetemp_id` (`messagetemp_id`,`mhluser_id`),
  KEY `mhluser_id_refs_user_ptr_id_3237f3ba9284a4f7` (`mhluser_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DoctorCom_messagetemp_user_recipients`
--

LOCK TABLES `DoctorCom_messagetemp_user_recipients` WRITE;
/*!40000 ALTER TABLE `DoctorCom_messagetemp_user_recipients` DISABLE KEYS */;
/*!40000 ALTER TABLE `DoctorCom_messagetemp_user_recipients` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `DoctorCom_pagerlog`
--

DROP TABLE IF EXISTS `DoctorCom_pagerlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DoctorCom_pagerlog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pager_id` int(11) DEFAULT NULL,
  `paged_id` int(11) NOT NULL,
  `current_site_id` int(11) DEFAULT NULL,
  `callback` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `DoctorCom_pagerlog_pager_id` (`pager_id`),
  KEY `DoctorCom_pagerlog_paged_id` (`paged_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DoctorCom_pagerlog`
--

LOCK TABLES `DoctorCom_pagerlog` WRITE;
/*!40000 ALTER TABLE `DoctorCom_pagerlog` DISABLE KEYS */;
/*!40000 ALTER TABLE `DoctorCom_pagerlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `DoctorCom_siteanalytics`
--

DROP TABLE IF EXISTS `DoctorCom_siteanalytics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DoctorCom_siteanalytics` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dateoflog` date NOT NULL,
  `site_id` int(11) DEFAULT NULL,
  `countPage` int(11) NOT NULL,
  `countMessage` int(11) NOT NULL,
  `countClick2Call` int(11) NOT NULL,
  `lastUpdate` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `dateoflog` (`dateoflog`,`site_id`),
  KEY `DoctorCom_siteanalytics_idx` (`site_id`),
  CONSTRAINT `site_id_refs_id_const` FOREIGN KEY (`site_id`) REFERENCES `MHLSites_site` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DoctorCom_siteanalytics`
--

LOCK TABLES `DoctorCom_siteanalytics` WRITE;
/*!40000 ALTER TABLE `DoctorCom_siteanalytics` DISABLE KEYS */;
/*!40000 ALTER TABLE `DoctorCom_siteanalytics` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `IVR_anssvcdlfailure`
--

DROP TABLE IF EXISTS `IVR_anssvcdlfailure`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `IVR_anssvcdlfailure` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `practice_id` int(11) NOT NULL,
  `error_timestamp` datetime NOT NULL,
  `resolved` tinyint(1) NOT NULL,
  `resolution_timestamp` datetime DEFAULT NULL,
  `failure_type` varchar(2) COLLATE utf8_unicode_ci NOT NULL DEFAULT 'DL',
  `post_data` longtext COLLATE utf8_unicode_ci NOT NULL,
  `call_sid` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `caller` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `called` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `recording_url` longtext COLLATE utf8_unicode_ci,
  `callback_number` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `error_message_uuid` varchar(32) COLLATE utf8_unicode_ci DEFAULT NULL,
  `resolution_message_uuid` varchar(32) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `IVR_anssvcdlfailure`
--

LOCK TABLES `IVR_anssvcdlfailure` WRITE;
/*!40000 ALTER TABLE `IVR_anssvcdlfailure` DISABLE KEYS */;
/*!40000 ALTER TABLE `IVR_anssvcdlfailure` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `IVR_anssvcdlfailureactivitylog`
--

DROP TABLE IF EXISTS `IVR_anssvcdlfailureactivitylog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `IVR_anssvcdlfailureactivitylog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `call_sid` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `timestamp` datetime NOT NULL,
  `action` varchar(3) COLLATE utf8_unicode_ci NOT NULL,
  `error_data` longtext COLLATE utf8_unicode_ci,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `IVR_anssvcdlfailureactivitylog`
--

LOCK TABLES `IVR_anssvcdlfailureactivitylog` WRITE;
/*!40000 ALTER TABLE `IVR_anssvcdlfailureactivitylog` DISABLE KEYS */;
/*!40000 ALTER TABLE `IVR_anssvcdlfailureactivitylog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `IVR_callevent`
--

DROP TABLE IF EXISTS `IVR_callevent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `IVR_callevent` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `callSID` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `event` varchar(5) COLLATE utf8_unicode_ci NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `IVR_callevent_callSID` (`callSID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `IVR_callevent`
--

LOCK TABLES `IVR_callevent` WRITE;
/*!40000 ALTER TABLE `IVR_callevent` DISABLE KEYS */;
/*!40000 ALTER TABLE `IVR_callevent` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `IVR_calleventtarget`
--

DROP TABLE IF EXISTS `IVR_calleventtarget`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `IVR_calleventtarget` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `event_id` int(11) NOT NULL,
  `target_type_id` int(11) NOT NULL,
  `target_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `event_id` (`event_id`),
  KEY `IVR_calleventtarget_target_type_id` (`target_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `IVR_calleventtarget`
--

LOCK TABLES `IVR_calleventtarget` WRITE;
/*!40000 ALTER TABLE `IVR_calleventtarget` DISABLE KEYS */;
/*!40000 ALTER TABLE `IVR_calleventtarget` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `IVR_calllog`
--

DROP TABLE IF EXISTS `IVR_calllog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `IVR_calllog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `caller_type_id` int(11) DEFAULT NULL,
  `caller_id` int(10) unsigned DEFAULT NULL,
  `caller_number` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `called_type_id` int(11) DEFAULT NULL,
  `called_id` int(10) unsigned DEFAULT NULL,
  `called_number` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `caller_spoken_name` longtext COLLATE utf8_unicode_ci NOT NULL,
  `callSID` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `call_connected` tinyint(1) NOT NULL,
  `c2c_entry_id` int(11) DEFAULT NULL,
  `call_duration` int(11) DEFAULT NULL,
  `timestamp` datetime NOT NULL,
  `call_source` varchar(2) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `callSID` (`callSID`),
  KEY `IVR_calllog_caller_type_id` (`caller_type_id`),
  KEY `IVR_calllog_called_type_id` (`called_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `IVR_calllog`
--

LOCK TABLES `IVR_calllog` WRITE;
/*!40000 ALTER TABLE `IVR_calllog` DISABLE KEYS */;
/*!40000 ALTER TABLE `IVR_calllog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `IVR_ivr_prompt`
--

DROP TABLE IF EXISTS `IVR_ivr_prompt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `IVR_ivr_prompt` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `practice_location_id` int(11) NOT NULL,
  `prompt` varchar(1) COLLATE utf8_unicode_ci NOT NULL,
  `prompt_verbage` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `practice_location_id` (`practice_location_id`,`prompt`),
  KEY `IVR_ivr_prompt_366c0f3e` (`practice_location_id`),
  CONSTRAINT `practice_location_id_refs_id_24231ea2` FOREIGN KEY (`practice_location_id`) REFERENCES `MHLPractices_practicelocation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `IVR_ivr_prompt`
--

LOCK TABLES `IVR_ivr_prompt` WRITE;
/*!40000 ALTER TABLE `IVR_ivr_prompt` DISABLE KEYS */;
/*!40000 ALTER TABLE `IVR_ivr_prompt` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `IVR_vmbox_config`
--

DROP TABLE IF EXISTS `IVR_vmbox_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `IVR_vmbox_config` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `owner_type_id` int(11) NOT NULL,
  `owner_id` int(10) unsigned NOT NULL,
  `pin` varchar(120) COLLATE utf8_unicode_ci NOT NULL,
  `name` longtext COLLATE utf8_unicode_ci NOT NULL,
  `greeting` longtext COLLATE utf8_unicode_ci NOT NULL,
  `config_complete` tinyint(1) NOT NULL,
  `notification_email` tinyint(1) NOT NULL,
  `notification_sms` int(1) DEFAULT '1',
  `notification_page` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `IVR_vmbox_config_owner_type_id` (`owner_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `IVR_vmbox_config`
--

LOCK TABLES `IVR_vmbox_config` WRITE;
/*!40000 ALTER TABLE `IVR_vmbox_config` DISABLE KEYS */;
INSERT INTO `IVR_vmbox_config` VALUES (1,52,1,'sha1$897f2$8cefb2926080697739931932d56cbde2c36b7a82','http://api.twilio.com/2008-08-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/REf8afc497f43d8e1e9bc229a415ebe100','http://api.twilio.com/2008-08-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/REf8afc497f43d8e1e9bc229a415ebe100',1,0,1,1);
/*!40000 ALTER TABLE `IVR_vmbox_config` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `IVR_vmmessage`
--

DROP TABLE IF EXISTS `IVR_vmmessage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `IVR_vmmessage` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `owner_type_id` int(11) NOT NULL,
  `owner_id` int(10) unsigned NOT NULL,
  `callerID` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `recording` longtext COLLATE utf8_unicode_ci NOT NULL,
  `deleted` tinyint(1) NOT NULL,
  `read_flag` tinyint(1) NOT NULL,
  `read_timestamp` datetime DEFAULT NULL,
  `timestamp` datetime NOT NULL,
  `answeringservice` tinyint(1) NOT NULL,
  `callbacknumber` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `IVR_vmmessage_owner_type_id` (`owner_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `IVR_vmmessage`
--

LOCK TABLES `IVR_vmmessage` WRITE;
/*!40000 ALTER TABLE `IVR_vmmessage` DISABLE KEYS */;
/*!40000 ALTER TABLE `IVR_vmmessage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Invites_invitation`
--

DROP TABLE IF EXISTS `Invites_invitation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Invites_invitation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(8) COLLATE utf8_unicode_ci NOT NULL,
  `sender_id` int(11) NOT NULL,
  `recipient` varchar(75) COLLATE utf8_unicode_ci NOT NULL,
  `userType` int(11) NOT NULL,
  `typeVerified` tinyint(1) NOT NULL,
  `createGroupPractice` tinyint(1) NOT NULL,
  `assignGroupPractice_id` int(11) DEFAULT NULL,
  `createPractice` tinyint(1) NOT NULL,
  `assignPractice_id` int(11) DEFAULT NULL,
  `identityVerified` int(1) DEFAULT '0',
  `requestTimestamp` datetime NOT NULL,
  `testFlag` tinyint(1) NOT NULL,
  `org_id` int(11) DEFAULT NULL,
  `org_role` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `Invites_invitation_sender_id` (`sender_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Invites_invitation`
--

LOCK TABLES `Invites_invitation` WRITE;
/*!40000 ALTER TABLE `Invites_invitation` DISABLE KEYS */;
/*!40000 ALTER TABLE `Invites_invitation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Invites_invitationlog`
--

DROP TABLE IF EXISTS `Invites_invitationlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Invites_invitationlog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(8) CHARACTER SET utf8 NOT NULL,
  `sender_id` int(11) NOT NULL,
  `recipient` varchar(75) CHARACTER SET utf8 NOT NULL,
  `userType` int(11) NOT NULL,
  `typeVerified` tinyint(1) NOT NULL,
  `requestTimestamp` datetime NOT NULL,
  `canceller_id` int(11) DEFAULT NULL,
  `responseTimestamp` datetime NOT NULL,
  `createdUser_id` int(11) DEFAULT NULL,
  `createdPractice_id` int(11) DEFAULT NULL,
  `testFlag` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Invites_invitationlog_sender_id` (`sender_id`),
  KEY `Invites_invitationlog_canceller_id` (`canceller_id`),
  KEY `Invites_invitationlog_createdUser_id` (`createdUser_id`),
  KEY `createdPractice_id_refs_id_7086dae5` (`createdPractice_id`),
  CONSTRAINT `createdPractice_id_refs_id_7086dae5` FOREIGN KEY (`createdPractice_id`) REFERENCES `MHLPractices_practicelocation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Invites_invitationlog`
--

LOCK TABLES `Invites_invitationlog` WRITE;
/*!40000 ALTER TABLE `Invites_invitationlog` DISABLE KEYS */;
/*!40000 ALTER TABLE `Invites_invitationlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `KMS_adminprivatekey`
--

DROP TABLE IF EXISTS `KMS_adminprivatekey`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `KMS_adminprivatekey` (
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `object_type_id` int(11) NOT NULL,
  `object_id` int(10) unsigned NOT NULL,
  `key` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`uuid`),
  KEY `object_type_id_refs_id_a738f6a6` (`object_type_id`),
  CONSTRAINT `object_type_id_refs_id_a738f6a6` FOREIGN KEY (`object_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `KMS_adminprivatekey`
--

LOCK TABLES `KMS_adminprivatekey` WRITE;
/*!40000 ALTER TABLE `KMS_adminprivatekey` DISABLE KEYS */;
/*!40000 ALTER TABLE `KMS_adminprivatekey` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `KMS_ivr_privatekey`
--

DROP TABLE IF EXISTS `KMS_ivr_privatekey`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `KMS_ivr_privatekey` (
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `owner_id` int(11) NOT NULL,
  `key` longtext COLLATE utf8_unicode_ci NOT NULL,
  `invalid_key` tinyint(1) NOT NULL,
  `object_type_id` int(11) NOT NULL,
  `object_id` int(11) NOT NULL,
  PRIMARY KEY (`uuid`),
  UNIQUE KEY `object_type_id` (`object_type_id`,`object_id`,`owner_id`),
  KEY `owner_id_refs_id_b357906` (`owner_id`),
  CONSTRAINT `object_type_id_refs_id_ee8b8496` FOREIGN KEY (`object_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `owner_id_refs_id_b357906` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `KMS_ivr_privatekey`
--

LOCK TABLES `KMS_ivr_privatekey` WRITE;
/*!40000 ALTER TABLE `KMS_ivr_privatekey` DISABLE KEYS */;
/*!40000 ALTER TABLE `KMS_ivr_privatekey` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `KMS_ivr_rsakeypair`
--

DROP TABLE IF EXISTS `KMS_ivr_rsakeypair`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `KMS_ivr_rsakeypair` (
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `owner_id` int(11) NOT NULL,
  `keypair` longtext COLLATE utf8_unicode_ci NOT NULL,
  `grandfathered` tinyint(1) NOT NULL,
  PRIMARY KEY (`uuid`),
  KEY `owner_id_refs_id_aeb883a1` (`owner_id`),
  CONSTRAINT `owner_id_refs_id_aeb883a1` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `KMS_ivr_rsakeypair`
--

LOCK TABLES `KMS_ivr_rsakeypair` WRITE;
/*!40000 ALTER TABLE `KMS_ivr_rsakeypair` DISABLE KEYS */;
/*!40000 ALTER TABLE `KMS_ivr_rsakeypair` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `KMS_ivr_rsapubkey`
--

DROP TABLE IF EXISTS `KMS_ivr_rsapubkey`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `KMS_ivr_rsapubkey` (
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `owner_id` int(11) NOT NULL,
  `public_key` longtext COLLATE utf8_unicode_ci NOT NULL,
  `key_pair_id` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`uuid`),
  KEY `owner_id_refs_id_d01d5d35` (`owner_id`),
  CONSTRAINT `owner_id_refs_id_d01d5d35` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `KMS_ivr_rsapubkey`
--

LOCK TABLES `KMS_ivr_rsapubkey` WRITE;
/*!40000 ALTER TABLE `KMS_ivr_rsapubkey` DISABLE KEYS */;
/*!40000 ALTER TABLE `KMS_ivr_rsapubkey` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `KMS_privatekey`
--

DROP TABLE IF EXISTS `KMS_privatekey`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `KMS_privatekey` (
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `object_type_id` int(11) NOT NULL,
  `object_id` int(10) unsigned NOT NULL,
  `owner_id` int(11) NOT NULL,
  `key` longtext COLLATE utf8_unicode_ci NOT NULL,
  `invalid_key` tinyint(1) NOT NULL,
  PRIMARY KEY (`uuid`),
  UNIQUE KEY `object_type_id` (`object_type_id`,`object_id`,`owner_id`),
  KEY `object_type_id_refs_id_4cb7085a` (`object_type_id`),
  KEY `owner_id_refs_id_7126f66a` (`owner_id`),
  CONSTRAINT `object_type_id_refs_id_4cb7085a` FOREIGN KEY (`object_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `owner_id_refs_id_7126f66a` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `KMS_privatekey`
--

LOCK TABLES `KMS_privatekey` WRITE;
/*!40000 ALTER TABLE `KMS_privatekey` DISABLE KEYS */;
/*!40000 ALTER TABLE `KMS_privatekey` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `KMS_rsakeypair`
--

DROP TABLE IF EXISTS `KMS_rsakeypair`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `KMS_rsakeypair` (
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `owner_id` int(11) NOT NULL,
  `keypair` longtext COLLATE utf8_unicode_ci NOT NULL,
  `grandfathered` tinyint(1) NOT NULL,
  `ivr_key_id` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`uuid`),
  UNIQUE KEY `owner_id` (`owner_id`),
  UNIQUE KEY `owner_id_2` (`owner_id`),
  KEY `ivr_key_id_refs_uuid_47f88d2d` (`ivr_key_id`),
  CONSTRAINT `ivr_key_id_refs_uuid_47f88d2d` FOREIGN KEY (`ivr_key_id`) REFERENCES `KMS_ivr_rsakeypair` (`uuid`),
  CONSTRAINT `owner_id_refs_id_cee9009f` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `KMS_rsakeypair`
--

LOCK TABLES `KMS_rsakeypair` WRITE;
/*!40000 ALTER TABLE `KMS_rsakeypair` DISABLE KEYS */;
/*!40000 ALTER TABLE `KMS_rsakeypair` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `KMS_rsapubkey`
--

DROP TABLE IF EXISTS `KMS_rsapubkey`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `KMS_rsapubkey` (
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `owner_id` int(11) NOT NULL,
  `public_key` longtext COLLATE utf8_unicode_ci NOT NULL,
  `ivr_key_id` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  `key_pair_id` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`uuid`),
  UNIQUE KEY `owner_id` (`owner_id`),
  UNIQUE KEY `key_pair_id` (`key_pair_id`),
  UNIQUE KEY `owner_id_2` (`owner_id`),
  UNIQUE KEY `key_pair_id_2` (`key_pair_id`),
  KEY `ivr_key_id_refs_uuid_60c9222d` (`ivr_key_id`),
  CONSTRAINT `ivr_key_id_refs_uuid_60c9222d` FOREIGN KEY (`ivr_key_id`) REFERENCES `KMS_ivr_rsapubkey` (`uuid`),
  CONSTRAINT `key_pair_id_refs_uuid_50b6a9b9` FOREIGN KEY (`key_pair_id`) REFERENCES `KMS_rsakeypair` (`uuid`),
  CONSTRAINT `owner_id_refs_id_b22a1f2d` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `KMS_rsapubkey`
--

LOCK TABLES `KMS_rsapubkey` WRITE;
/*!40000 ALTER TABLE `KMS_rsapubkey` DISABLE KEYS */;
/*!40000 ALTER TABLE `KMS_rsapubkey` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `KMS_securetestmessage`
--

DROP TABLE IF EXISTS `KMS_securetestmessage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `KMS_securetestmessage` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `owner_id` int(11) DEFAULT NULL,
  `ciphertext` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `owner_id_refs_id_48bc83f1` (`owner_id`),
  CONSTRAINT `owner_id_refs_id_48bc83f1` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `KMS_securetestmessage`
--

LOCK TABLES `KMS_securetestmessage` WRITE;
/*!40000 ALTER TABLE `KMS_securetestmessage` DISABLE KEYS */;
/*!40000 ALTER TABLE `KMS_securetestmessage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Logs_loginevent`
--

DROP TABLE IF EXISTS `Logs_loginevent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Logs_loginevent` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` datetime NOT NULL,
  `username` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `remote_ip` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
  `success` tinyint(1) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `Logs_loginevent_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Logs_loginevent`
--

LOCK TABLES `Logs_loginevent` WRITE;
/*!40000 ALTER TABLE `Logs_loginevent` DISABLE KEYS */;
/*!40000 ALTER TABLE `Logs_loginevent` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Logs_logoutevent`
--

DROP TABLE IF EXISTS `Logs_logoutevent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Logs_logoutevent` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` datetime NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Logs_logoutevent_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Logs_logoutevent`
--

LOCK TABLES `Logs_logoutevent` WRITE;
/*!40000 ALTER TABLE `Logs_logoutevent` DISABLE KEYS */;
/*!40000 ALTER TABLE `Logs_logoutevent` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLCallGroups_callgroup`
--

DROP TABLE IF EXISTS `MHLCallGroups_callgroup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLCallGroups_callgroup` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `description` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `team` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `number_selection` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLCallGroups_callgroup`
--

LOCK TABLES `MHLCallGroups_callgroup` WRITE;
/*!40000 ALTER TABLE `MHLCallGroups_callgroup` DISABLE KEYS */;
INSERT INTO `MHLCallGroups_callgroup` VALUES (1,'test practice','',NULL),(2,'Smile Bright','',NULL),(3,'Berlin Dentistry','',NULL),(4,'DoctorCom Berlin','',NULL),(5,'DENS','',NULL);
/*!40000 ALTER TABLE `MHLCallGroups_callgroup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLCallGroups_callgroupmember`
--

DROP TABLE IF EXISTS `MHLCallGroups_callgroupmember`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLCallGroups_callgroupmember` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `call_group_id` int(11) DEFAULT NULL,
  `member_id` int(11) DEFAULT NULL,
  `alt_provider` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `call_group_id` (`call_group_id`,`member_id`),
  UNIQUE KEY `call_group_id_2` (`call_group_id`,`member_id`),
  KEY `MHLCallGroups_callgroupmember_3999cf1a` (`call_group_id`),
  KEY `MHLCallGroups_callgroupmember_56e38b98` (`member_id`),
  CONSTRAINT `call_group_id_refs_id_5f8db307` FOREIGN KEY (`call_group_id`) REFERENCES `MHLCallGroups_callgroup` (`id`),
  CONSTRAINT `member_id_refs_mhluser_ptr_id_1d6b0f8d` FOREIGN KEY (`member_id`) REFERENCES `MHLUsers_provider` (`mhluser_ptr_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLCallGroups_callgroupmember`
--

LOCK TABLES `MHLCallGroups_callgroupmember` WRITE;
/*!40000 ALTER TABLE `MHLCallGroups_callgroupmember` DISABLE KEYS */;
INSERT INTO `MHLCallGroups_callgroupmember` VALUES (1,8,30,1);
/*!40000 ALTER TABLE `MHLCallGroups_callgroupmember` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLCallGroups_callgroupmemberpending`
--

DROP TABLE IF EXISTS `MHLCallGroups_callgroupmemberpending`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLCallGroups_callgroupmemberpending` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `call_group_id` int(11) DEFAULT NULL,
  `practice_id` int(11) DEFAULT NULL,
  `from_user_id` int(11) NOT NULL,
  `to_user_id` int(11) NOT NULL,
  `created_time` datetime NOT NULL,
  `resent_time` datetime DEFAULT NULL,
  `accept_status` int(1) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLCallGroups_callgroupmemberpending`
--

LOCK TABLES `MHLCallGroups_callgroupmemberpending` WRITE;
/*!40000 ALTER TABLE `MHLCallGroups_callgroupmemberpending` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLCallGroups_callgroupmemberpending` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLCallGroups_specialty`
--

DROP TABLE IF EXISTS `MHLCallGroups_specialty`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLCallGroups_specialty` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `practice_location_id` int(11) NOT NULL,
  `number_selection` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `MHLCallGroups_specialty_366c0f3e` (`practice_location_id`),
  CONSTRAINT `practice_location_id_refs_id_7b190ed3` FOREIGN KEY (`practice_location_id`) REFERENCES `MHLPractices_practicelocation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLCallGroups_specialty`
--

LOCK TABLES `MHLCallGroups_specialty` WRITE;
/*!40000 ALTER TABLE `MHLCallGroups_specialty` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLCallGroups_specialty` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLCallGroups_specialty_call_groups`
--

DROP TABLE IF EXISTS `MHLCallGroups_specialty_call_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLCallGroups_specialty_call_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `specialty_id` int(11) NOT NULL,
  `callgroup_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `specialty_id` (`specialty_id`,`callgroup_id`),
  KEY `callgroup_id_refs_id_18a4a044` (`callgroup_id`),
  CONSTRAINT `callgroup_id_refs_id_18a4a044` FOREIGN KEY (`callgroup_id`) REFERENCES `MHLCallGroups_callgroup` (`id`),
  CONSTRAINT `specialty_id_refs_id_94e355d` FOREIGN KEY (`specialty_id`) REFERENCES `MHLCallGroups_specialty` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLCallGroups_specialty_call_groups`
--

LOCK TABLES `MHLCallGroups_specialty_call_groups` WRITE;
/*!40000 ALTER TABLE `MHLCallGroups_specialty_call_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLCallGroups_specialty_call_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLGroups_mhlgroup`
--

DROP TABLE IF EXISTS `MHLGroups_mhlgroup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLGroups_mhlgroup` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLGroups_mhlgroup`
--

LOCK TABLES `MHLGroups_mhlgroup` WRITE;
/*!40000 ALTER TABLE `MHLGroups_mhlgroup` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLGroups_mhlgroup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLGroups_mhlgroupmember`
--

DROP TABLE IF EXISTS `MHLGroups_mhlgroupmember`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLGroups_mhlgroupmember` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  `join_date` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`group_id`),
  KEY `MHLGroups_mhlgroupmember_user_id` (`user_id`),
  KEY `MHLGroups_mhlgroupmember_group_id` (`group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLGroups_mhlgroupmember`
--

LOCK TABLES `MHLGroups_mhlgroupmember` WRITE;
/*!40000 ALTER TABLE `MHLGroups_mhlgroupmember` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLGroups_mhlgroupmember` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLOrg_organization`
--

DROP TABLE IF EXISTS `MHLOrg_organization`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLOrg_organization` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `logo` varchar(255) COLLATE utf8_unicode_ci DEFAULT '',
  `logo_position` int(11) DEFAULT '0',
  `logo_size` int(11) DEFAULT '0',
  `description` varchar(255) COLLATE utf8_unicode_ci DEFAULT '',
  `has_refer` tinyint(1) NOT NULL DEFAULT '0',
  `refer_pay_time` datetime DEFAULT NULL,
  `refer_pay_status` tinyint(1) NOT NULL DEFAULT '0',
  `create_date` datetime NOT NULL,
  `org_status` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLOrg_organization`
--

LOCK TABLES `MHLOrg_organization` WRITE;
/*!40000 ALTER TABLE `MHLOrg_organization` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLOrg_organization` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLOrg_organization_member`
--

DROP TABLE IF EXISTS `MHLOrg_organization_member`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLOrg_organization_member` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `mhluser_id` int(11) NOT NULL,
  `org_id` int(11) NOT NULL,
  `role` int(11) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `mhluser_id` (`mhluser_id`,`org_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLOrg_organization_member`
--

LOCK TABLES `MHLOrg_organization_member` WRITE;
/*!40000 ALTER TABLE `MHLOrg_organization_member` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLOrg_organization_member` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLOrg_pending_organization`
--

DROP TABLE IF EXISTS `MHLOrg_pending_organization`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLOrg_pending_organization` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `from_user_id` int(11) NOT NULL,
  `to_user_id` int(11) NOT NULL,
  `org_id` int(11) NOT NULL,
  `role` int(11) DEFAULT '0',
  `created_time` datetime NOT NULL,
  `resent_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLOrg_pending_organization`
--

LOCK TABLES `MHLOrg_pending_organization` WRITE;
/*!40000 ALTER TABLE `MHLOrg_pending_organization` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLOrg_pending_organization` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLPractices_accessnumber`
--

DROP TABLE IF EXISTS `MHLPractices_accessnumber`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLPractices_accessnumber` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `practice_id` int(11) NOT NULL,
  `description` varchar(50) NOT NULL,
  `number` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `practice_id_refs_id_cb985732` (`practice_id`),
  CONSTRAINT `practice_id_refs_id_cb985732` FOREIGN KEY (`practice_id`) REFERENCES `MHLPractices_practicelocation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLPractices_accessnumber`
--

LOCK TABLES `MHLPractices_accessnumber` WRITE;
/*!40000 ALTER TABLE `MHLPractices_accessnumber` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLPractices_accessnumber` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLPractices_accountactivecode`
--

DROP TABLE IF EXISTS `MHLPractices_accountactivecode`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLPractices_accountactivecode` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `sender` int(11) NOT NULL,
  `recipient` varchar(75) COLLATE utf8_unicode_ci NOT NULL,
  `userType` int(11) NOT NULL,
  `requestTimestamp` datetime NOT NULL,
  `practice_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLPractices_accountactivecode`
--

LOCK TABLES `MHLPractices_accountactivecode` WRITE;
/*!40000 ALTER TABLE `MHLPractices_accountactivecode` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLPractices_accountactivecode` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLPractices_log_association`
--

DROP TABLE IF EXISTS `MHLPractices_log_association`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLPractices_log_association` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `association_id` int(11) NOT NULL,
  `from_user_id` int(11) NOT NULL,
  `to_user_id` int(11) NOT NULL,
  `practice_location_id` int(11) NOT NULL,
  `action_user_id` int(11) NOT NULL,
  `action` varchar(3) COLLATE utf8_unicode_ci NOT NULL,
  `created_time` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `MHLPractices_log_association_8b4ff41f` (`from_user_id`),
  KEY `MHLPractices_log_association_ceab885c` (`to_user_id`),
  KEY `MHLPractices_log_association_366c0f3e` (`practice_location_id`),
  KEY `MHLPractices_log_association_26679921` (`action_user_id`),
  CONSTRAINT `action_user_id_refs_user_ptr_id_5e1510eb` FOREIGN KEY (`action_user_id`) REFERENCES `MHLUsers_mhluser` (`user_ptr_id`),
  CONSTRAINT `from_user_id_refs_user_ptr_id_5e1510eb` FOREIGN KEY (`from_user_id`) REFERENCES `MHLUsers_mhluser` (`user_ptr_id`),
  CONSTRAINT `practice_location_id_refs_id_ce1bd814` FOREIGN KEY (`practice_location_id`) REFERENCES `MHLPractices_practicelocation` (`id`),
  CONSTRAINT `to_user_id_refs_user_ptr_id_5e1510eb` FOREIGN KEY (`to_user_id`) REFERENCES `MHLUsers_mhluser` (`user_ptr_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLPractices_log_association`
--

LOCK TABLES `MHLPractices_log_association` WRITE;
/*!40000 ALTER TABLE `MHLPractices_log_association` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLPractices_log_association` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLPractices_log_org_association`
--

DROP TABLE IF EXISTS `MHLPractices_log_org_association`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLPractices_log_org_association` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `association_id` int(11) NOT NULL,
  `from_practicelocation_id` int(11) NOT NULL,
  `to_practicelocation_id` int(11) NOT NULL,
  `sender_id` int(11) NOT NULL,
  `action_user_id` int(11) NOT NULL,
  `action` varchar(3) COLLATE utf8_unicode_ci NOT NULL,
  `create_time` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `from_practicelocation_id_refs_id_5571d403` (`from_practicelocation_id`),
  KEY `to_practicelocation_id_refs_id_5571d403` (`to_practicelocation_id`),
  CONSTRAINT `from_practicelocation_id_refs_id_5571d403` FOREIGN KEY (`from_practicelocation_id`) REFERENCES `MHLPractices_practicelocation` (`id`),
  CONSTRAINT `to_practicelocation_id_refs_id_5571d403` FOREIGN KEY (`to_practicelocation_id`) REFERENCES `MHLPractices_practicelocation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLPractices_log_org_association`
--

LOCK TABLES `MHLPractices_log_org_association` WRITE;
/*!40000 ALTER TABLE `MHLPractices_log_org_association` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLPractices_log_org_association` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLPractices_organizationrelationship`
--

DROP TABLE IF EXISTS `MHLPractices_organizationrelationship`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLPractices_organizationrelationship` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `organization_id` int(11) NOT NULL,
  `parent_id` int(11) DEFAULT NULL,
  `create_time` int(10) unsigned NOT NULL,
  `billing_flag` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `organization_id` (`organization_id`,`parent_id`),
  KEY `parent_id_refs_id_580b63ac` (`parent_id`),
  CONSTRAINT `organization_id_refs_id_580b63ac` FOREIGN KEY (`organization_id`) REFERENCES `MHLPractices_practicelocation` (`id`),
  CONSTRAINT `parent_id_refs_id_580b63ac` FOREIGN KEY (`parent_id`) REFERENCES `MHLPractices_practicelocation` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLPractices_organizationrelationship`
--

LOCK TABLES `MHLPractices_organizationrelationship` WRITE;
/*!40000 ALTER TABLE `MHLPractices_organizationrelationship` DISABLE KEYS */;
INSERT INTO `MHLPractices_organizationrelationship` VALUES (1,-1,NULL,1363169712,NULL),(2,1,-1,1363169712,NULL);
/*!40000 ALTER TABLE `MHLPractices_organizationrelationship` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLPractices_organizationsetting`
--

DROP TABLE IF EXISTS `MHLPractices_organizationsetting`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLPractices_organizationsetting` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `can_have_answering_service` tinyint(1) NOT NULL DEFAULT '0',
  `can_be_billed` tinyint(1) NOT NULL DEFAULT '0',
  `display_in_contact_list_tab` tinyint(1) NOT NULL DEFAULT '0',
  `can_have_luxury_logo` tinyint(1) NOT NULL DEFAULT '0',
  `can_have_member_organization` tinyint(1) NOT NULL DEFAULT '0',
  `can_have_physician` tinyint(1) NOT NULL DEFAULT '0',
  `can_have_nppa` tinyint(1) NOT NULL DEFAULT '0',
  `can_have_medical_student` tinyint(1) NOT NULL DEFAULT '0',
  `can_have_staff` tinyint(1) NOT NULL DEFAULT '0',
  `can_have_manager` tinyint(1) NOT NULL DEFAULT '0',
  `can_have_nurse` tinyint(1) NOT NULL DEFAULT '0',
  `can_have_dietician` tinyint(1) NOT NULL DEFAULT '0',
  `can_have_tech_admin` tinyint(1) NOT NULL DEFAULT '0',
  `delete_flag` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLPractices_organizationsetting`
--

LOCK TABLES `MHLPractices_organizationsetting` WRITE;
/*!40000 ALTER TABLE `MHLPractices_organizationsetting` DISABLE KEYS */;
INSERT INTO `MHLPractices_organizationsetting` VALUES (-1,1,1,0,0,0,1,1,1,1,1,1,1,1,0),(1,1,1,0,0,0,1,1,1,1,1,1,1,1,0),(2,1,1,0,0,0,1,1,1,1,1,1,1,1,0),(3,1,1,0,0,0,1,1,1,1,1,1,1,1,0),(4,1,1,1,1,1,1,1,1,1,1,1,1,1,0);
/*!40000 ALTER TABLE `MHLPractices_organizationsetting` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLPractices_organizationtype`
--

DROP TABLE IF EXISTS `MHLPractices_organizationtype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLPractices_organizationtype` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `is_public` tinyint(1) NOT NULL DEFAULT '0',
  `description` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `organization_setting_id` int(11) NOT NULL,
  `delete_flag` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `name` (`name`),
  KEY `organization_setting_id_refs_id_3be3c2ea` (`organization_setting_id`),
  CONSTRAINT `organization_setting_id_refs_id_3be3c2ea` FOREIGN KEY (`organization_setting_id`) REFERENCES `MHLPractices_organizationsetting` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLPractices_organizationtype`
--

LOCK TABLES `MHLPractices_organizationtype` WRITE;
/*!40000 ALTER TABLE `MHLPractices_organizationtype` DISABLE KEYS */;
INSERT INTO `MHLPractices_organizationtype` VALUES (-1,'8fe57c2f5ede4d96bb25827c1005f7ee','System',0,'default type',-1,0),(1,'1fe57c2f5ede4d96bb25827c1005f7ee','Arztpraxis',1,'',1,0),(2,'2fe57c2f5ede4d96bb25827c1005f7ee','Praxisnetzwerk',1,'',2,0),(3,'3fe57c2f5ede4d96bb25827c1005f7ee','Krankenhaus',1,'',3,0),(4,'4fe57c2f5ede4d96bb25827c1005f7ee','Gesundheitsnetzwerk',1,'',4,0);
UNLOCK TABLES;

--
-- Table structure for table `MHLPractices_organizationtype_subs`
--

DROP TABLE IF EXISTS `MHLPractices_organizationtype_subs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLPractices_organizationtype_subs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `from_organizationtype_id` int(11) NOT NULL,
  `to_organizationtype_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `from_organizationtype_id` (`from_organizationtype_id`,`to_organizationtype_id`),
  KEY `to_organizationtype_id_refs_id_45f93918` (`to_organizationtype_id`),
  CONSTRAINT `from_organizationtype_id_refs_id_45f93918` FOREIGN KEY (`from_organizationtype_id`) REFERENCES `MHLPractices_organizationtype` (`id`),
  CONSTRAINT `to_organizationtype_id_refs_id_45f93918` FOREIGN KEY (`to_organizationtype_id`) REFERENCES `MHLPractices_organizationtype` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLPractices_organizationtype_subs`
--

LOCK TABLES `MHLPractices_organizationtype_subs` WRITE;
/*!40000 ALTER TABLE `MHLPractices_organizationtype_subs` DISABLE KEYS */;
INSERT INTO `MHLPractices_organizationtype_subs` VALUES (1,-1,1),(2,-1,2),(3,-1,3),(4,-1,4),(5,2,1),(6,3,1),(7,3,2),(8,4,4);
/*!40000 ALTER TABLE `MHLPractices_organizationtype_subs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLPractices_pending_association`
--

DROP TABLE IF EXISTS `MHLPractices_pending_association`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLPractices_pending_association` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `from_user_id` int(11) NOT NULL,
  `to_user_id` int(11) NOT NULL,
  `practice_location_id` int(11) NOT NULL,
  `created_time` datetime NOT NULL,
  `resent_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `MHLPractices_pending_association_8b4ff41f` (`from_user_id`),
  KEY `MHLPractices_pending_association_ceab885c` (`to_user_id`),
  KEY `MHLPractices_pending_association_366c0f3e` (`practice_location_id`),
  CONSTRAINT `from_user_id_refs_user_ptr_id_1c8126cc` FOREIGN KEY (`from_user_id`) REFERENCES `MHLUsers_mhluser` (`user_ptr_id`),
  CONSTRAINT `practice_location_id_refs_id_1c9b820b` FOREIGN KEY (`practice_location_id`) REFERENCES `MHLPractices_practicelocation` (`id`),
  CONSTRAINT `to_user_id_refs_user_ptr_id_1c8126cc` FOREIGN KEY (`to_user_id`) REFERENCES `MHLUsers_mhluser` (`user_ptr_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLPractices_pending_association`
--

LOCK TABLES `MHLPractices_pending_association` WRITE;
/*!40000 ALTER TABLE `MHLPractices_pending_association` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLPractices_pending_association` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLPractices_pending_org_association`
--

DROP TABLE IF EXISTS `MHLPractices_pending_org_association`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLPractices_pending_org_association` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `from_practicelocation_id` int(11) NOT NULL,
  `to_practicelocation_id` int(11) NOT NULL,
  `sender_id` int(11) NOT NULL,
  `create_time` int(10) unsigned NOT NULL,
  `resent_time` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `from_practicelocation_id_refs_id_d243e8c` (`from_practicelocation_id`),
  KEY `to_practicelocation_id_refs_id_d243e8c` (`to_practicelocation_id`),
  CONSTRAINT `from_practicelocation_id_refs_id_d243e8c` FOREIGN KEY (`from_practicelocation_id`) REFERENCES `MHLPractices_practicelocation` (`id`),
  CONSTRAINT `to_practicelocation_id_refs_id_d243e8c` FOREIGN KEY (`to_practicelocation_id`) REFERENCES `MHLPractices_practicelocation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLPractices_pending_org_association`
--

LOCK TABLES `MHLPractices_pending_org_association` WRITE;
/*!40000 ALTER TABLE `MHLPractices_pending_org_association` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLPractices_pending_org_association` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLPractices_practicegroup`
--

DROP TABLE IF EXISTS `MHLPractices_practicegroup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLPractices_practicegroup` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `description` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `address` longtext COLLATE utf8_unicode_ci,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLPractices_practicegroup`
--

LOCK TABLES `MHLPractices_practicegroup` WRITE;
/*!40000 ALTER TABLE `MHLPractices_practicegroup` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLPractices_practicegroup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLPractices_practiceholidays`
--

DROP TABLE IF EXISTS `MHLPractices_practiceholidays`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLPractices_practiceholidays` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `practice_location_id` int(11) NOT NULL,
  `name` varchar(34) COLLATE utf8_unicode_ci NOT NULL,
  `designated_day` date NOT NULL,
  PRIMARY KEY (`id`),
  KEY `MHLPractices_practiceholidays_366c0f3e` (`practice_location_id`),
  CONSTRAINT `practice_location_id_refs_id_435c6723` FOREIGN KEY (`practice_location_id`) REFERENCES `MHLPractices_practicelocation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLPractices_practiceholidays`
--

LOCK TABLES `MHLPractices_practiceholidays` WRITE;
/*!40000 ALTER TABLE `MHLPractices_practiceholidays` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLPractices_practiceholidays` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLPractices_practicehours`
--

DROP TABLE IF EXISTS `MHLPractices_practicehours`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLPractices_practicehours` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `practice_location_id` int(11) NOT NULL,
  `day_of_week` int(11) NOT NULL,
  `open` time NOT NULL,
  `close` time NOT NULL,
  `lunch_start` time NOT NULL,
  `lunch_duration` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `MHLPractices_practicehours_366c0f3e` (`practice_location_id`),
  CONSTRAINT `practice_location_id_refs_id_7dbd62f4` FOREIGN KEY (`practice_location_id`) REFERENCES `MHLPractices_practicelocation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLPractices_practicehours`
--

LOCK TABLES `MHLPractices_practicehours` WRITE;
/*!40000 ALTER TABLE `MHLPractices_practicehours` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLPractices_practicehours` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLPractices_practicelocation`
--

DROP TABLE IF EXISTS `MHLPractices_practicelocation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLPractices_practicelocation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `practice_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `practice_address1` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `practice_address2` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `practice_phone` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `practice_city` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `practice_state` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `practice_zip` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `practice_lat` double NOT NULL,
  `practice_longit` double NOT NULL,
  `mdcom_phone` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `mdcom_phone_sid` varchar(34) COLLATE utf8_unicode_ci NOT NULL,
  `time_zone` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `call_group_id` int(11) DEFAULT NULL,
  `pin` varchar(120) COLLATE utf8_unicode_ci DEFAULT NULL,
  `name_greeting` longtext COLLATE utf8_unicode_ci,
  `greeting_closed` longtext COLLATE utf8_unicode_ci,
  `greeting_lunch` longtext COLLATE utf8_unicode_ci,
  `config_complete` tinyint(1) DEFAULT NULL,
  `practice_photo` varchar(100) COLLATE utf8_unicode_ci DEFAULT '',
  `practice_group_id` int(11) DEFAULT NULL,
  `skip_to_rmsg` tinyint(1) NOT NULL DEFAULT '0',
  `gen_msg` tinyint(1) NOT NULL,
  `backline_phone` varchar(20) COLLATE utf8_unicode_ci DEFAULT '',
  `logo_position` int(11) DEFAULT '0',
  `logo_size` int(11) DEFAULT '0',
  `description` varchar(255) COLLATE utf8_unicode_ci DEFAULT '',
  `create_date` datetime NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT '1',
  `short_name` varchar(30) COLLATE utf8_unicode_ci DEFAULT '',
  `organization_type_id` int(11) DEFAULT NULL,
  `organization_setting_id` int(11) DEFAULT NULL,
  `delete_flag` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `practice_name` (`practice_name`),
  KEY `call_group_id_refs_id_7ace645a` (`call_group_id`),
  KEY `practicelocation_ibfk_1` (`practice_group_id`),
  KEY `organization_setting_id_refs_id_641732d1` (`organization_setting_id`),
  KEY `organization_type_id_refs_id_6ef32e00` (`organization_type_id`),
  CONSTRAINT `call_group_id_refs_id_7ace645a` FOREIGN KEY (`call_group_id`) REFERENCES `MHLCallGroups_callgroup` (`id`),
  CONSTRAINT `organization_setting_id_refs_id_641732d1` FOREIGN KEY (`organization_setting_id`) REFERENCES `MHLPractices_organizationsetting` (`id`),
  CONSTRAINT `organization_type_id_refs_id_6ef32e00` FOREIGN KEY (`organization_type_id`) REFERENCES `MHLPractices_organizationtype` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLPractices_practicelocation`
--

LOCK TABLES `MHLPractices_practicelocation` WRITE;
/*!40000 ALTER TABLE `MHLPractices_practicelocation` DISABLE KEYS */;
INSERT INTO `MHLPractices_practicelocation` VALUES (-1,'DC system','','','','','','',0,0,'','','',NULL,'','','','',0,'',NULL,0,1,'',0,0,NULL,'2013-01-30 15:38:06',1,'',-1,NULL,0),(1,'test practice','Hauptstrae 82','','','wacken','','24869',37.522337,-81.806919,'','','Europe/Berlin',1,'','','','',0,'',NULL,0,0,'',0,0,'','0000-00-00 00:00:00',1,'',1,NULL,0),(2,'Smile Bright','Burgstrasse 28','','','','BE','10178',40.799925,-73.971668,'','','Atlantic/Reykjavik',2,'','','','',0,'',NULL,0,0,'',0,0,'','0000-00-00 00:00:00',1,'',1,NULL,0),(3,'Berlin Dentistry','Alexanderstrasse 5','','','','BE','10178',40.799925,-73.971668,'','','Atlantic/Reykjavik',3,'','','','',0,'',NULL,0,0,'',0,0,'','0000-00-00 00:00:00',1,'',1,NULL,0),(4,'DoctorCom Berlin','Zillestrasse 71','','','','BE','10585',52.516642,13.30888,'','','Europe/Berlin',4,'','','','',0,'',NULL,0,0,'',0,0,'','2013-04-25 05:09:41',1,'',1,NULL,0),(5,'DENS','Berliner Str. 13','','','','BE','14513',43.050575,-77.094329,'','','Europe/Berlin',5,'','','','',0,'',NULL,0,0,'',0,0,'','0000-00-00 00:00:00',1,'',1,NULL,0);
/*!40000 ALTER TABLE `MHLPractices_practicelocation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLPractices_practicelocation_call_groups`
--

DROP TABLE IF EXISTS `MHLPractices_practicelocation_call_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLPractices_practicelocation_call_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `practicelocation_id` int(11) NOT NULL,
  `callgroup_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `practicelocation_id` (`practicelocation_id`,`callgroup_id`),
  KEY `callgroup_id_refs_id_6346189c` (`callgroup_id`),
  CONSTRAINT `callgroup_id_refs_id_6346189c` FOREIGN KEY (`callgroup_id`) REFERENCES `MHLCallGroups_callgroup` (`id`),
  CONSTRAINT `practicelocation_id_refs_id_7005108d` FOREIGN KEY (`practicelocation_id`) REFERENCES `MHLPractices_practicelocation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLPractices_practicelocation_call_groups`
--

LOCK TABLES `MHLPractices_practicelocation_call_groups` WRITE;
/*!40000 ALTER TABLE `MHLPractices_practicelocation_call_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLPractices_practicelocation_call_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLPractices_practicelocation_member_orgs`
--

DROP TABLE IF EXISTS `MHLPractices_practicelocation_member_orgs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLPractices_practicelocation_member_orgs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `from_practicelocation_id` int(11) NOT NULL,
  `to_practicelocation_id` int(11) NOT NULL,
  `create_time` int(10) unsigned NOT NULL,
  `billing_flag` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `from_practicelocation_id` (`from_practicelocation_id`,`to_practicelocation_id`),
  KEY `to_practicelocation_id_refs_id_2fbacf88` (`to_practicelocation_id`),
  CONSTRAINT `from_practicelocation_id_refs_id_2fbacf88` FOREIGN KEY (`from_practicelocation_id`) REFERENCES `MHLPractices_practicelocation` (`id`),
  CONSTRAINT `to_practicelocation_id_refs_id_2fbacf88` FOREIGN KEY (`to_practicelocation_id`) REFERENCES `MHLPractices_practicelocation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLPractices_practicelocation_member_orgs`
--

LOCK TABLES `MHLPractices_practicelocation_member_orgs` WRITE;
/*!40000 ALTER TABLE `MHLPractices_practicelocation_member_orgs` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLPractices_practicelocation_member_orgs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLSites_hospital`
--

DROP TABLE IF EXISTS `MHLSites_hospital`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLSites_hospital` (
  `site_ptr_id` int(11) NOT NULL,
  PRIMARY KEY (`site_ptr_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLSites_hospital`
--

LOCK TABLES `MHLSites_hospital` WRITE;
/*!40000 ALTER TABLE `MHLSites_hospital` DISABLE KEYS */;

/*!40000 ALTER TABLE `MHLSites_hospital` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLSites_site`
--

DROP TABLE IF EXISTS `MHLSites_site`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLSites_site` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `address1` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `address2` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `city` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `state` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `zip` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `lat` double DEFAULT NULL,
  `long` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `longit` double NOT NULL,
  `short_name` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLSites_site`
--

LOCK TABLES `MHLSites_site` WRITE;
/*!40000 ALTER TABLE `MHLSites_site` DISABLE KEYS */;
INSERT INTO `MHLSites_site` VALUES (1,'Charité','Charité Universitätsmedizin','','Berlin','BE','10117',46,'',2,'c');
/*!40000 ALTER TABLE `MHLSites_site` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_administrator`
--

DROP TABLE IF EXISTS `MHLUsers_administrator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_administrator` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_administrator`
--

LOCK TABLES `MHLUsers_administrator` WRITE;
/*!40000 ALTER TABLE `MHLUsers_administrator` DISABLE KEYS */;
INSERT INTO `MHLUsers_administrator` VALUES (1,1);
/*!40000 ALTER TABLE `MHLUsers_administrator` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_broker`
--

DROP TABLE IF EXISTS `MHLUsers_broker`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_broker` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT NULL,
  `office_address1` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `office_address2` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `office_phone` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `office_city` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `office_state` varchar(2) COLLATE utf8_unicode_ci DEFAULT NULL,
  `office_zip` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `office_lat` double DEFAULT NULL,
  `office_longit` double DEFAULT NULL,
  `pager` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `pager_extension` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `pager_confirmed` tinyint(1) NOT NULL,
  `mdcom_phone` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `mdcom_phone_sid` varchar(34) COLLATE utf8_unicode_ci NOT NULL,
  `forward_other` tinyint(1) NOT NULL,
  `forward_mobile` tinyint(1) NOT NULL,
  `forward_office` tinyint(1) NOT NULL,
  `forward_vmail` tinyint(1) NOT NULL,
  `forward_voicemail` varchar(2) COLLATE utf8_unicode_ci NOT NULL DEFAULT 'MO',
  `forward_anssvc` varchar(2) COLLATE utf8_unicode_ci NOT NULL DEFAULT 'VM',
  `current_practice_id` int(11) DEFAULT NULL,
  `status_verified` tinyint(1) DEFAULT NULL,
  `status_verifier_id` int(11) DEFAULT NULL,
  `clinical_clerk` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `mhlusers_broker_ibfk_1` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_broker`
--

LOCK TABLES `MHLUsers_broker` WRITE;
/*!40000 ALTER TABLE `MHLUsers_broker` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLUsers_broker` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_broker_licensure_states`
--

DROP TABLE IF EXISTS `MHLUsers_broker_licensure_states`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_broker_licensure_states` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `broker_id` int(11) NOT NULL,
  `states_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `broker_id` (`broker_id`,`states_id`),
  KEY `states_id_refs_id_1` (`states_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_broker_licensure_states`
--

LOCK TABLES `MHLUsers_broker_licensure_states` WRITE;
/*!40000 ALTER TABLE `MHLUsers_broker_licensure_states` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLUsers_broker_licensure_states` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_dietician`
--

DROP TABLE IF EXISTS `MHLUsers_dietician`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_dietician` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `user_id_refs_id_1c2a96fb` FOREIGN KEY (`user_id`) REFERENCES `MHLUsers_officestaff` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_dietician`
--

LOCK TABLES `MHLUsers_dietician` WRITE;
/*!40000 ALTER TABLE `MHLUsers_dietician` DISABLE KEYS */;

/*!40000 ALTER TABLE `MHLUsers_dietician` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_eventlog`
--

DROP TABLE IF EXISTS `MHLUsers_eventlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_eventlog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `event` varchar(2000) COLLATE utf8_unicode_ci NOT NULL,
  `date` datetime NOT NULL,
  `staff` varchar(1) COLLATE utf8_unicode_ci NOT NULL,
  `staff_type` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `sent_message` varchar(1) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `MHLUsers_eventlog_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_eventlog`
--

LOCK TABLES `MHLUsers_eventlog` WRITE;
/*!40000 ALTER TABLE `MHLUsers_eventlog` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLUsers_eventlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_mhluser`
--

DROP TABLE IF EXISTS `MHLUsers_mhluser`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_mhluser` (
  `user_ptr_id` int(11) NOT NULL,
  `gender` varchar(1) COLLATE utf8_unicode_ci NOT NULL,
  `phone` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `mobile_phone` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `address1` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `address2` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `city` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `state` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `zip` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `lat` double DEFAULT NULL,
  `longit` double DEFAULT NULL,
  `photo` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `email_confirmed` tinyint(1) NOT NULL,
  `mobile_confirmed` tinyint(1) NOT NULL,
  `tos_accepted` tinyint(1) NOT NULL,
  `billing_account_accepted` tinyint(1) NOT NULL,
  `force_pass_change` tinyint(1) NOT NULL,
  `password_change_time` datetime NOT NULL DEFAULT '1970-01-01 00:00:00',
  `skill` varchar(200) COLLATE utf8_unicode_ci DEFAULT NULL,
  `time_setting` int(11) DEFAULT '0',
  `time_zone` varchar(64) COLLATE utf8_unicode_ci DEFAULT NULL,
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `partner_creator_id` int(11) DEFAULT NULL,
  `public_notes` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`user_ptr_id`),
  UNIQUE KEY `uk_user_uuid` (`uuid`),
  KEY `partner_creator_id_refs_id_2275a059` (`partner_creator_id`),
  CONSTRAINT `partner_creator_id_refs_id_2275a059` FOREIGN KEY (`partner_creator_id`) REFERENCES `Partners_partner` (`id`)
) ENGINE=InnoDB CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_mhluser`
--

LOCK TABLES `MHLUsers_mhluser` WRITE;
/*!40000 ALTER TABLE `MHLUsers_mhluser` DISABLE KEYS */;
INSERT INTO `MHLUsers_mhluser` VALUES (1,'M','8005555555','8005555555','berlin','berlin','berlin','','10115',52.531944,13.383785,'images/userBioPics/2012/08/21/demo.png',1,1,1,0,0,'2012-06-28 19:00:14',
NULL,0,NULL,'f4e15132ab2011e2abd30285955b0714',NULL,''),(2,'M','','','','','Dorpstedt','SH','24869',54.43235,9.35292,'',1,0,1,0,0,'2013-03-05 20:55:30',NULL,0,NULL,'f4e152c2ab2011e2abd30285955b0714',NULL,'');
/*!40000 ALTER TABLE `MHLUsers_mhluser` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_np_pa`
--

DROP TABLE IF EXISTS `MHLUsers_np_pa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_np_pa` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_np_pa`
--

LOCK TABLES `MHLUsers_np_pa` WRITE;
/*!40000 ALTER TABLE `MHLUsers_np_pa` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLUsers_np_pa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_nurse`
--

DROP TABLE IF EXISTS `MHLUsers_nurse`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_nurse` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `user_id_refs_id_5bb31f1c` FOREIGN KEY (`user_id`) REFERENCES `MHLUsers_officestaff` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_nurse`
--

LOCK TABLES `MHLUsers_nurse` WRITE;
/*!40000 ALTER TABLE `MHLUsers_nurse` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLUsers_nurse` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_office_manager`
--

DROP TABLE IF EXISTS `MHLUsers_office_manager`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_office_manager` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `practice_id` int(11) NOT NULL,
  `manager_role` int(11) DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_practice` (`user_id`,`practice_id`),
  KEY `practice_id_refs_id_27d8fceb` (`practice_id`),
  CONSTRAINT `practice_id_refs_id_27d8fceb` FOREIGN KEY (`practice_id`) REFERENCES `MHLPractices_practicelocation` (`id`),
  CONSTRAINT `user_id_refs_id_39d3d8e` FOREIGN KEY (`user_id`) REFERENCES `MHLUsers_officestaff` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_office_manager`
--

LOCK TABLES `MHLUsers_office_manager` WRITE;
/*!40000 ALTER TABLE `MHLUsers_office_manager` DISABLE KEYS */;
INSERT INTO `MHLUsers_office_manager` VALUES (1,1,1,1);
/*!40000 ALTER TABLE `MHLUsers_office_manager` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_officestaff`
--

DROP TABLE IF EXISTS `MHLUsers_officestaff`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_officestaff` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT NULL,
  `office_address1` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `office_address2` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `office_phone` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `office_city` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `office_state` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `office_zip` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `pager` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `pager_extension` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `pager_confirmed` tinyint(1) NOT NULL,
  `current_site_id` int(11) DEFAULT NULL,
  `current_practice_id` int(11) DEFAULT NULL,
  `caller_anssvc` varchar(2) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `MHLUsers_officestaff_403f60f` (`user_id`),
  KEY `MHLUsers_officestaff_6fb53dfb` (`current_site_id`),
  KEY `MHLUsers_officestaff_7287c005` (`current_practice_id`),
  CONSTRAINT `current_practice_id_refs_id_c3364b2` FOREIGN KEY (`current_practice_id`) REFERENCES `MHLPractices_practicelocation` (`id`),
  CONSTRAINT `current_site_id_refs_id_c4a40e5` FOREIGN KEY (`current_site_id`) REFERENCES `MHLSites_site` (`id`),
  CONSTRAINT `user_id_refs_user_ptr_id_4ca93c41` FOREIGN KEY (`user_id`) REFERENCES `MHLUsers_mhluser` (`user_ptr_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_officestaff`
--

LOCK TABLES `MHLUsers_officestaff` WRITE;
/*!40000 ALTER TABLE `MHLUsers_officestaff` DISABLE KEYS */;
INSERT INTO `MHLUsers_officestaff` VALUES (1,2,'','','','','','','','',0,NULL,1,'');
/*!40000 ALTER TABLE `MHLUsers_officestaff` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_officestaff_practices`
--

DROP TABLE IF EXISTS `MHLUsers_officestaff_practices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_officestaff_practices` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `officestaff_id` int(11) NOT NULL,
  `practicelocation_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `officestaff_id` (`officestaff_id`,`practicelocation_id`),
  KEY `practicelocation_id_refs_id_251881c5` (`practicelocation_id`),
  CONSTRAINT `officestaff_id_refs_id_68ab8b9e` FOREIGN KEY (`officestaff_id`) REFERENCES `MHLUsers_officestaff` (`id`),
  CONSTRAINT `practicelocation_id_refs_id_251881c5` FOREIGN KEY (`practicelocation_id`) REFERENCES `MHLPractices_practicelocation` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_officestaff_practices`
--

LOCK TABLES `MHLUsers_officestaff_practices` WRITE;
/*!40000 ALTER TABLE `MHLUsers_officestaff_practices` DISABLE KEYS */;
INSERT INTO `MHLUsers_officestaff_practices` VALUES (1,1,1);
/*!40000 ALTER TABLE `MHLUsers_officestaff_practices` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_officestaff_sites`
--

DROP TABLE IF EXISTS `MHLUsers_officestaff_sites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_officestaff_sites` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `officestaff_id` int(11) NOT NULL,
  `site_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `officestaff_id` (`officestaff_id`,`site_id`),
  KEY `site_id_refs_id_74ca7d42` (`site_id`),
  CONSTRAINT `officestaff_id_refs_id_79f40988` FOREIGN KEY (`officestaff_id`) REFERENCES `MHLUsers_officestaff` (`id`),
  CONSTRAINT `site_id_refs_id_74ca7d42` FOREIGN KEY (`site_id`) REFERENCES `MHLSites_site` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_officestaff_sites`
--

LOCK TABLES `MHLUsers_officestaff_sites` WRITE;
/*!40000 ALTER TABLE `MHLUsers_officestaff_sites` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLUsers_officestaff_sites` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_passwordresetlog`
--

DROP TABLE IF EXISTS `MHLUsers_passwordresetlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_passwordresetlog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `reset` tinyint(1) NOT NULL,
  `resolved` tinyint(1) NOT NULL,
  `requestor_id` int(11) DEFAULT NULL,
  `requestor_ip` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `request_timestamp` datetime NOT NULL,
  `code` varchar(32) COLLATE utf8_unicode_ci NOT NULL,
  `reset_ip` char(15) COLLATE utf8_unicode_ci DEFAULT NULL,
  `reset_timestamp` datetime DEFAULT NULL,
  `servicer_id` int(11) DEFAULT NULL,
  `servicer_ip` char(15) COLLATE utf8_unicode_ci DEFAULT NULL,
  `resolution_timestamp` datetime DEFAULT NULL,
  `security_answers_count` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id_refs_id_b92fcbcf` (`user_id`),
  KEY `requestor_id_refs_id_b92fcbcf` (`requestor_id`),
  KEY `servicer_id_refs_id_b92fcbcf` (`servicer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_passwordresetlog`
--

LOCK TABLES `MHLUsers_passwordresetlog` WRITE;
/*!40000 ALTER TABLE `MHLUsers_passwordresetlog` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLUsers_passwordresetlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_patient`
--

DROP TABLE IF EXISTS `MHLUsers_patient`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_patient` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `room_number` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `care_type` varchar(1) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_patient`
--

LOCK TABLES `MHLUsers_patient` WRITE;
/*!40000 ALTER TABLE `MHLUsers_patient` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLUsers_patient` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_physician`
--

DROP TABLE IF EXISTS `MHLUsers_physician`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_physician` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `specialty` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `accepting_new_patients` tinyint(1) NOT NULL,
  `staff_type` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_physician`
--

LOCK TABLES `MHLUsers_physician` WRITE;
/*!40000 ALTER TABLE `MHLUsers_physician` DISABLE KEYS */;
INSERT INTO `MHLUsers_physician` VALUES (1,1,'MG',1,'CR');
/*!40000 ALTER TABLE `MHLUsers_physician` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_physiciangroup`
--

DROP TABLE IF EXISTS `MHLUsers_physiciangroup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_physiciangroup` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_physiciangroup`
--

LOCK TABLES `MHLUsers_physiciangroup` WRITE;
/*!40000 ALTER TABLE `MHLUsers_physiciangroup` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLUsers_physiciangroup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_physiciangroupmembers`
--

DROP TABLE IF EXISTS `MHLUsers_physiciangroupmembers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_physiciangroupmembers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `physician_id` int(11) NOT NULL,
  `physician_group_id` int(11) NOT NULL,
  `joined_date` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `MHLUsers_physiciangroupmembers_physician_id` (`physician_id`),
  KEY `MHLUsers_physiciangroupmembers_physician_group_id` (`physician_group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_physiciangroupmembers`
--

LOCK TABLES `MHLUsers_physiciangroupmembers` WRITE;
/*!40000 ALTER TABLE `MHLUsers_physiciangroupmembers` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLUsers_physiciangroupmembers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_provider`
--

DROP TABLE IF EXISTS `MHLUsers_provider`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_provider` (
  `mhluser_ptr_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `office_address1` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `office_address2` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `office_phone` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `office_city` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `office_state` varchar(2) COLLATE utf8_unicode_ci DEFAULT NULL,
  `office_zip` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `office_lat` double DEFAULT NULL,
  `office_longit` double DEFAULT NULL,
  `pager` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `pager_extension` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `pager_confirmed` tinyint(1) NOT NULL,
  `mdcom_phone` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `mdcom_phone_sid` varchar(34) COLLATE utf8_unicode_ci NOT NULL,
  `forward_other` tinyint(1) NOT NULL,
  `forward_mobile` tinyint(1) NOT NULL,
  `forward_office` tinyint(1) NOT NULL,
  `forward_vmail` tinyint(1) NOT NULL,
  `forward_voicemail` varchar(2) COLLATE utf8_unicode_ci NOT NULL DEFAULT 'MO',
  `forward_anssvc` varchar(2) COLLATE utf8_unicode_ci NOT NULL DEFAULT 'VM',
  `current_site_id` int(11) DEFAULT NULL,
  `current_practice_id` int(11) DEFAULT NULL,
  `clinical_clerk` tinyint(1) NOT NULL,
  `status_verified` tinyint(1) DEFAULT NULL,
  `status_verifier_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`mhluser_ptr_id`),
  KEY `MHLUsers_provider_current_site_id` (`current_site_id`),
  KEY `MHLUsers_provider_user_id` (`user_id`),
  KEY `MHLUsers_provider_7287c005` (`current_practice_id`),
  CONSTRAINT `current_practice_id_refs_id_738a5196` FOREIGN KEY (`current_practice_id`) REFERENCES `MHLPractices_practicelocation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_provider`
--

LOCK TABLES `MHLUsers_provider` WRITE;
/*!40000 ALTER TABLE `MHLUsers_provider` DISABLE KEYS */;
INSERT INTO `MHLUsers_provider` VALUES (1,1,'1','','','1','BB','22333',38.815392,-77.064132,'','',0,'6503197996','PN11e6d58448904d7aaefb1ec47fd21780',1,0,0,0,'OT','VM',1,1,0,0,NULL);
/*!40000 ALTER TABLE `MHLUsers_provider` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_provider_licensure_states`
--

DROP TABLE IF EXISTS `MHLUsers_provider_licensure_states`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_provider_licensure_states` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `provider_id` int(11) NOT NULL,
  `states_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `provider_id` (`provider_id`,`states_id`),
  KEY `states_id_refs_id_575041d` (`states_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_provider_licensure_states`
--

LOCK TABLES `MHLUsers_provider_licensure_states` WRITE;
/*!40000 ALTER TABLE `MHLUsers_provider_licensure_states` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLUsers_provider_licensure_states` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_provider_practices`
--

DROP TABLE IF EXISTS `MHLUsers_provider_practices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_provider_practices` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `provider_id` int(11) NOT NULL,
  `practicelocation_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `provider_id` (`provider_id`,`practicelocation_id`),
  KEY `practicelocation_id_refs_id_67d3d8cf` (`practicelocation_id`),
  CONSTRAINT `practicelocation_id_refs_id_67d3d8cf` FOREIGN KEY (`practicelocation_id`) REFERENCES `MHLPractices_practicelocation` (`id`),
  CONSTRAINT `provider_id_refs_mhluser_ptr_id_3232ca4e` FOREIGN KEY (`provider_id`) REFERENCES `MHLUsers_provider` (`mhluser_ptr_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_provider_practices`
--

LOCK TABLES `MHLUsers_provider_practices` WRITE;
/*!40000 ALTER TABLE `MHLUsers_provider_practices` DISABLE KEYS */;
INSERT INTO `MHLUsers_provider_practices` VALUES (1,1,1);
/*!40000 ALTER TABLE `MHLUsers_provider_practices` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_provider_sites`
--

DROP TABLE IF EXISTS `MHLUsers_provider_sites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_provider_sites` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `provider_id` int(11) NOT NULL,
  `site_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `provider_id` (`provider_id`,`site_id`),
  KEY `site_id_refs_id_2b25c47b467d8d9a` (`site_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_provider_sites`
--

LOCK TABLES `MHLUsers_provider_sites` WRITE;
/*!40000 ALTER TABLE `MHLUsers_provider_sites` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLUsers_provider_sites` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_quicksignupuser`
--

DROP TABLE IF EXISTS `MHLUsers_quicksignupuser`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_quicksignupuser` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `user_id_refs_user_ptr_id_3284355f` FOREIGN KEY (`user_id`) REFERENCES `MHLUsers_mhluser` (`user_ptr_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_quicksignupuser`
--

LOCK TABLES `MHLUsers_quicksignupuser` WRITE;
/*!40000 ALTER TABLE `MHLUsers_quicksignupuser` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLUsers_quicksignupuser` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_regional_manager`
--

DROP TABLE IF EXISTS `MHLUsers_regional_manager`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_regional_manager` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `office_mgr_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `office_mgr_id_refs_id_fe7416bc` (`office_mgr_id`),
  CONSTRAINT `office_mgr_id_refs_id_fe7416bc` FOREIGN KEY (`office_mgr_id`) REFERENCES `MHLUsers_office_manager` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_regional_manager`
--

LOCK TABLES `MHLUsers_regional_manager` WRITE;
/*!40000 ALTER TABLE `MHLUsers_regional_manager` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLUsers_regional_manager` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_securityquestions`
--

DROP TABLE IF EXISTS `MHLUsers_securityquestions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_securityquestions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `security_question1` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `security_question2` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `security_question3` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `security_answer1` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `security_answer2` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `security_answer3` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `MHLUsers_securityquesions_403f60f` (`user_id`),
  CONSTRAINT `user_id_refs_id_69151772` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_securityquestions`
--

LOCK TABLES `MHLUsers_securityquestions` WRITE;
/*!40000 ALTER TABLE `MHLUsers_securityquestions` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLUsers_securityquestions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_states`
--

DROP TABLE IF EXISTS `MHLUsers_states`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_states` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nation` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `state` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nation` (`nation`,`state`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_states`
--

LOCK TABLES `MHLUsers_states` WRITE;
/*!40000 ALTER TABLE `MHLUsers_states` DISABLE KEYS */;
INSERT INTO `MHLUsers_states` VALUES (4,'de','BB'),(3,'de','BE'),(1,'de','BW'),(2,'de','BY'),(5,'de','HB'),(7,'de','HE'),(6,'de','HH'),(8,'de','MV'),(9,'de','NI'),(10,'de','NW'),(11,'de','RP'),(15,'de','SH'),(12,'de','SL'),(13,'de','SN'),(14,'de','ST'),(16,'de','TH');
/*!40000 ALTER TABLE `MHLUsers_states` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MHLUsers_userprofile`
--

DROP TABLE IF EXISTS `MHLUsers_userprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MHLUsers_userprofile` (
  `mhluser_ptr_id` int(11) NOT NULL,
  PRIMARY KEY (`mhluser_ptr_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MHLUsers_userprofile`
--

LOCK TABLES `MHLUsers_userprofile` WRITE;
/*!40000 ALTER TABLE `MHLUsers_userprofile` DISABLE KEYS */;
/*!40000 ALTER TABLE `MHLUsers_userprofile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Messaging_callbacklog`
--

DROP TABLE IF EXISTS `Messaging_callbacklog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Messaging_callbacklog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `message_id` int(11) NOT NULL,
  `time` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `message_id_refs_id_c99e10a7` (`message_id`),
  CONSTRAINT `message_id_refs_id_c99e10a7` FOREIGN KEY (`message_id`) REFERENCES `Messaging_message` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Messaging_callbacklog`
--

LOCK TABLES `Messaging_callbacklog` WRITE;
/*!40000 ALTER TABLE `Messaging_callbacklog` DISABLE KEYS */;
/*!40000 ALTER TABLE `Messaging_callbacklog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Messaging_message`
--

DROP TABLE IF EXISTS `Messaging_message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Messaging_message` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `sender_id` int(11) DEFAULT NULL,
  `urgent` tinyint(1) NOT NULL,
  `draft` tinyint(1) NOT NULL,
  `send_timestamp` int(10) unsigned NOT NULL,
  `sender_site_id` int(11) DEFAULT NULL,
  `subject` varchar(1024) COLLATE utf8_unicode_ci DEFAULT NULL,
  `related_message_id` int(11) DEFAULT NULL,
  `related_message_relation` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `_resolved_by_id` int(11) DEFAULT NULL,
  `resolution_timestamp` int(10) unsigned NOT NULL,
  `message_type` varchar(3) COLLATE utf8_unicode_ci NOT NULL,
  `callback_number` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `vmstatus` varchar(1) COLLATE utf8_unicode_ci NOT NULL,
  `thread_uuid` varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `sender_id_refs_id_64bc6b2f` (`sender_id`),
  KEY `sender_site_id_refs_id_2ea09f80` (`sender_site_id`),
  KEY `related_message_id_refs_id_7d50de25` (`related_message_id`),
  CONSTRAINT `related_message_id_refs_id_7d50de25` FOREIGN KEY (`related_message_id`) REFERENCES `Messaging_message` (`id`),
  CONSTRAINT `sender_id_refs_id_64bc6b2f` FOREIGN KEY (`sender_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `sender_site_id_refs_id_2ea09f80` FOREIGN KEY (`sender_site_id`) REFERENCES `MHLSites_site` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Messaging_message`
--

LOCK TABLES `Messaging_message` WRITE;
/*!40000 ALTER TABLE `Messaging_message` DISABLE KEYS */;
/*!40000 ALTER TABLE `Messaging_message` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Messaging_message_ccs`
--

DROP TABLE IF EXISTS `Messaging_message_ccs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Messaging_message_ccs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `message_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `message_id` (`message_id`,`user_id`),
  KEY `user_id_refs_id_c94d2ff5` (`user_id`),
  CONSTRAINT `message_id_refs_id_460f5cff` FOREIGN KEY (`message_id`) REFERENCES `Messaging_message` (`id`),
  CONSTRAINT `user_id_refs_id_c94d2ff5` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Messaging_message_ccs`
--

LOCK TABLES `Messaging_message_ccs` WRITE;
/*!40000 ALTER TABLE `Messaging_message_ccs` DISABLE KEYS */;
/*!40000 ALTER TABLE `Messaging_message_ccs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Messaging_message_recipients`
--

DROP TABLE IF EXISTS `Messaging_message_recipients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Messaging_message_recipients` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `message_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `message_id` (`message_id`,`user_id`),
  KEY `user_id_refs_id_50340d5b` (`user_id`),
  CONSTRAINT `message_id_refs_id_40620127` FOREIGN KEY (`message_id`) REFERENCES `Messaging_message` (`id`),
  CONSTRAINT `user_id_refs_id_50340d5b` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Messaging_message_recipients`
--

LOCK TABLES `Messaging_message_recipients` WRITE;
/*!40000 ALTER TABLE `Messaging_message_recipients` DISABLE KEYS */;
/*!40000 ALTER TABLE `Messaging_message_recipients` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Messaging_messageattachment`
--

DROP TABLE IF EXISTS `Messaging_messageattachment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Messaging_messageattachment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `message_id` int(11) NOT NULL,
  `uuid` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `filename` longtext COLLATE utf8_unicode_ci NOT NULL,
  `url` longtext COLLATE utf8_unicode_ci NOT NULL,
  `encrypted` tinyint(1) NOT NULL,
  `content_type` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `encoding` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `charset` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `suffix` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `size` int(10) unsigned NOT NULL,
  `metadata` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `message_id_refs_id_612a95dc` (`message_id`),
  CONSTRAINT `message_id_refs_id_612a95dc` FOREIGN KEY (`message_id`) REFERENCES `Messaging_message` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Messaging_messageattachment`
--

LOCK TABLES `Messaging_messageattachment` WRITE;
/*!40000 ALTER TABLE `Messaging_messageattachment` DISABLE KEYS */;
/*!40000 ALTER TABLE `Messaging_messageattachment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Messaging_messageattachmentdicom`
--

DROP TABLE IF EXISTS `Messaging_messageattachmentdicom`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Messaging_messageattachmentdicom` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `attachment_id` int(11) NOT NULL,
  `jpg_count` int(10) unsigned NOT NULL,
  `xml_count` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `attachment_id` (`attachment_id`),
  CONSTRAINT `attachment_id_refs_id_6a53f952` FOREIGN KEY (`attachment_id`) REFERENCES `Messaging_messageattachment` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Messaging_messageattachmentdicom`
--

LOCK TABLES `Messaging_messageattachmentdicom` WRITE;
/*!40000 ALTER TABLE `Messaging_messageattachmentdicom` DISABLE KEYS */;
/*!40000 ALTER TABLE `Messaging_messageattachmentdicom` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Messaging_messagebody`
--

DROP TABLE IF EXISTS `Messaging_messagebody`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Messaging_messagebody` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `message_id` int(11) NOT NULL,
  `body` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `message_id_refs_id_788c3b3d` (`message_id`),
  CONSTRAINT `message_id_refs_id_788c3b3d` FOREIGN KEY (`message_id`) REFERENCES `Messaging_message` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Messaging_messagebody`
--

LOCK TABLES `Messaging_messagebody` WRITE;
/*!40000 ALTER TABLE `Messaging_messagebody` DISABLE KEYS */;
/*!40000 ALTER TABLE `Messaging_messagebody` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Messaging_messagebodyuserstatus`
--

DROP TABLE IF EXISTS `Messaging_messagebodyuserstatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Messaging_messagebodyuserstatus` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `msg_body_id` int(11) NOT NULL,
  `read_flag` tinyint(1) NOT NULL,
  `read_timestamp` int(10) unsigned NOT NULL,
  `delete_flag` tinyint(1) NOT NULL,
  `delete_timestamp` int(10) unsigned NOT NULL,
  `resolution_flag` tinyint(1) NOT NULL,
  `resolution_timestamp` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`msg_body_id`),
  KEY `user_id_refs_id_85f28ac8` (`user_id`),
  KEY `msg_body_id_refs_id_44cde74` (`msg_body_id`),
  CONSTRAINT `msg_body_id_refs_id_44cde74` FOREIGN KEY (`msg_body_id`) REFERENCES `Messaging_messagebody` (`id`),
  CONSTRAINT `user_id_refs_id_85f28ac8` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Messaging_messagebodyuserstatus`
--

LOCK TABLES `Messaging_messagebodyuserstatus` WRITE;
/*!40000 ALTER TABLE `Messaging_messagebodyuserstatus` DISABLE KEYS */;
/*!40000 ALTER TABLE `Messaging_messagebodyuserstatus` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Messaging_messagerefer`
--

DROP TABLE IF EXISTS `Messaging_messagerefer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Messaging_messagerefer` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `message_id` int(11) NOT NULL,
  `first_name` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `middle_name` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL,
  `last_name` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `gender` varchar(1) COLLATE utf8_unicode_ci NOT NULL,
  `date_of_birth` date DEFAULT NULL,
  `phone_number` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `alternative_phone_number` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `insurance_id` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL,
  `insurance_name` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL,
  `is_sendfax` tinyint(1) NOT NULL,
  `status` varchar(2) COLLATE utf8_unicode_ci NOT NULL,
  `uuid` varchar(32) COLLATE utf8_unicode_ci DEFAULT NULL,
  `refer_pdf` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `refer_jpg` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `refuse_reason` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `secondary_insurance_id` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL,
  `secondary_insurance_name` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL,
  `tertiary_insurance_id` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL,
  `tertiary_insurance_name` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL,
  `practice_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `messaging_messagerefer_ibfk_1` (`message_id`),
  KEY `practicelocation_messagerefer_ibfk_1` (`practice_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Messaging_messagerefer`
--

LOCK TABLES `Messaging_messagerefer` WRITE;
/*!40000 ALTER TABLE `Messaging_messagerefer` DISABLE KEYS */;
/*!40000 ALTER TABLE `Messaging_messagerefer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `NumberProvisioner_numberpool`
--

DROP TABLE IF EXISTS `NumberProvisioner_numberpool`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `NumberProvisioner_numberpool` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `number_sid` varchar(34) CHARACTER SET utf8 NOT NULL,
  `area_code` varchar(3) CHARACTER SET utf8 NOT NULL,
  `prefix` varchar(3) CHARACTER SET utf8 NOT NULL,
  `line_number` varchar(4) CHARACTER SET utf8 NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `area_code` (`area_code`,`prefix`,`line_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `NumberProvisioner_numberpool`
--

LOCK TABLES `NumberProvisioner_numberpool` WRITE;
/*!40000 ALTER TABLE `NumberProvisioner_numberpool` DISABLE KEYS */;
/*!40000 ALTER TABLE `NumberProvisioner_numberpool` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Partners_partner`
--

DROP TABLE IF EXISTS `Partners_partner`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Partners_partner` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `mhluser_id` int(11) NOT NULL,
  `partner_name` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `permission` int(11) NOT NULL,
  `token` longtext COLLATE utf8_unicode_ci NOT NULL,
  `api_secret` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `mhluser_id` (`mhluser_id`),
  UNIQUE KEY `partner_name` (`partner_name`),
  CONSTRAINT `mhluser_id_refs_user_ptr_id_3778c4a7` FOREIGN KEY (`mhluser_id`) REFERENCES `MHLUsers_mhluser` (`user_ptr_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Partners_partner`
--

LOCK TABLES `Partners_partner` WRITE;
/*!40000 ALTER TABLE `Partners_partner` DISABLE KEYS */;
/*!40000 ALTER TABLE `Partners_partner` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Partners_partneraccounts`
--

DROP TABLE IF EXISTS `Partners_partneraccounts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Partners_partneraccounts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `partner_id` int(11) NOT NULL,
  `mhluser_id` int(11) NOT NULL,
  `joined_time` datetime NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `partner_id` (`partner_id`,`mhluser_id`),
  KEY `mhluser_id_refs_user_ptr_id_69bdb5a9` (`mhluser_id`),
  CONSTRAINT `mhluser_id_refs_user_ptr_id_69bdb5a9` FOREIGN KEY (`mhluser_id`) REFERENCES `MHLUsers_mhluser` (`user_ptr_id`),
  CONSTRAINT `partner_id_refs_id_fbf3287` FOREIGN KEY (`partner_id`) REFERENCES `Partners_partner` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Partners_partneraccounts`
--

LOCK TABLES `Partners_partneraccounts` WRITE;
/*!40000 ALTER TABLE `Partners_partneraccounts` DISABLE KEYS */;
/*!40000 ALTER TABLE `Partners_partneraccounts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Partners_partnerip`
--

DROP TABLE IF EXISTS `Partners_partnerip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Partners_partnerip` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `partner_id` int(11) NOT NULL,
  `ip_address` char(15) COLLATE utf8_unicode_ci NOT NULL,
  `description` varchar(256) COLLATE utf8_unicode_ci NOT NULL,
  `joined_time` datetime NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `partner_id_refs_id_6647046a` (`partner_id`),
  CONSTRAINT `partner_id_refs_id_6647046a` FOREIGN KEY (`partner_id`) REFERENCES `Partners_partner` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Partners_partnerip`
--

LOCK TABLES `Partners_partnerip` WRITE;
/*!40000 ALTER TABLE `Partners_partnerip` DISABLE KEYS */;
/*!40000 ALTER TABLE `Partners_partnerip` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Partners_partnerlog`
--

DROP TABLE IF EXISTS `Partners_partnerlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Partners_partnerlog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `partner_id` int(11) DEFAULT NULL,
  `mhluser_id` int(11) DEFAULT NULL,
  `request_ip` char(15) COLLATE utf8_unicode_ci NOT NULL,
  `request_api` varchar(128) COLLATE utf8_unicode_ci NOT NULL,
  `status_code` int(11) NOT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime NOT NULL,
  `error_no` varchar(16) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `partner_id_refs_id_51a7012e` (`partner_id`),
  KEY `mhluser_id_refs_user_ptr_id_3cdaaf5e` (`mhluser_id`),
  CONSTRAINT `mhluser_id_refs_user_ptr_id_3cdaaf5e` FOREIGN KEY (`mhluser_id`) REFERENCES `MHLUsers_mhluser` (`user_ptr_id`),
  CONSTRAINT `partner_id_refs_id_51a7012e` FOREIGN KEY (`partner_id`) REFERENCES `Partners_partner` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Partners_partnerlog`
--

LOCK TABLES `Partners_partnerlog` WRITE;
/*!40000 ALTER TABLE `Partners_partnerlog` DISABLE KEYS */;
/*!40000 ALTER TABLE `Partners_partnerlog` ENABLE KEYS */;
UNLOCK TABLES;
-- Table structure for table `SMS_senderlookup`
--

DROP TABLE IF EXISTS `SMS_senderlookup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SMS_senderlookup` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `mapped_user_id` int(11) DEFAULT NULL,
  `number` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `mapped_user_id` (`mapped_user_id`,`number`),
  KEY `user_id_refs_user_ptr_id_ccb7f4b2` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SMS_senderlookup`
--

LOCK TABLES `SMS_senderlookup` WRITE;
/*!40000 ALTER TABLE `SMS_senderlookup` DISABLE KEYS */;
/*!40000 ALTER TABLE `SMS_senderlookup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Sales_products`
--

DROP TABLE IF EXISTS `Sales_products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Sales_products` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `description` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `code` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `price` decimal(20,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  UNIQUE KEY `code_2` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Sales_products`
--

LOCK TABLES `Sales_products` WRITE;
/*!40000 ALTER TABLE `Sales_products` DISABLE KEYS */;
INSERT INTO `Sales_products` VALUES (1,'File-Sharing','fsh_srv','50.00'),(2,'Skilled Nursing Facility Messaging & Telephony','snf_msg','200.00'),(3,'Set-Up Fee','set_up','50.00'),(4,'Answering Service','ans_ser','55.00');
/*!40000 ALTER TABLE `Sales_products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Sales_salesleads`
--

DROP TABLE IF EXISTS `Sales_salesleads`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Sales_salesleads` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `practice` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `region` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `salestype` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `rep_id` int(11) DEFAULT NULL,
  `contact` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `phone` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `email` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `website` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `date_contact` date NOT NULL,
  `date_appt` date NOT NULL,
  `price` decimal(20,2) NOT NULL,
  `stage` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `notes` longtext COLLATE utf8_unicode_ci NOT NULL,
  `address` longtext COLLATE utf8_unicode_ci NOT NULL,
  `date_of_billing` date DEFAULT NULL,
  `date_of_training` date DEFAULT NULL,
  `source` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `rep_id_refs_user_ptr_id_f204fa1` (`rep_id`),
  CONSTRAINT `rep_id_refs_user_ptr_id_f204fa1` FOREIGN KEY (`rep_id`) REFERENCES `MHLUsers_mhluser` (`user_ptr_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Sales_salesleads`
--

LOCK TABLES `Sales_salesleads` WRITE;
/*!40000 ALTER TABLE `Sales_salesleads` DISABLE KEYS */;
/*!40000 ALTER TABLE `Sales_salesleads` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Sales_salesperson`
--

DROP TABLE IF EXISTS `Sales_salesperson`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Sales_salesperson` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Sales_salesperson`
--

LOCK TABLES `Sales_salesperson` WRITE;
/*!40000 ALTER TABLE `Sales_salesperson` DISABLE KEYS */;
/*!40000 ALTER TABLE `Sales_salesperson` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Sales_salesproduct`
--

DROP TABLE IF EXISTS `Sales_salesproduct`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Sales_salesproduct` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `is_active` tinyint(1) NOT NULL,
  `lead_id` int(11) DEFAULT NULL,
  `product_id` int(11) DEFAULT NULL,
  `quoted_price` decimal(20,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `lead_id_refs_id_57a65f7b` (`lead_id`),
  KEY `product_id_refs_id_898f7730` (`product_id`),
  CONSTRAINT `product_id_refs_id_898f7730` FOREIGN KEY (`product_id`) REFERENCES `Sales_products` (`id`),
  CONSTRAINT `lead_id_refs_id_57a65f7b` FOREIGN KEY (`lead_id`) REFERENCES `Sales_salesleads` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Sales_salesproduct`
--

LOCK TABLES `Sales_salesproduct` WRITE;
/*!40000 ALTER TABLE `Sales_salesproduct` DISABLE KEYS */;
/*!40000 ALTER TABLE `Sales_salesproduct` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Scheduler_evententry`
--

DROP TABLE IF EXISTS `Scheduler_evententry`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Scheduler_evententry` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `callGroup_id` int(11) NOT NULL,
  `title` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `startDate` datetime NOT NULL,
  `endDate` datetime NOT NULL,
  `eventType` varchar(1) COLLATE utf8_unicode_ci NOT NULL,
  `oncallPerson_id` int(11) NOT NULL,
  `oncallLevel` varchar(1) COLLATE utf8_unicode_ci NOT NULL,
  `oncallStatus` varchar(1) COLLATE utf8_unicode_ci NOT NULL,
  `creator_id` int(11) NOT NULL,
  `creationdate` datetime NOT NULL,
  `lastupdate` datetime NOT NULL,
  `eventStatus` varchar(1) COLLATE utf8_unicode_ci NOT NULL,
  `notifyState` varchar(1) COLLATE utf8_unicode_ci NOT NULL,
  `whoCanModify` varchar(1) COLLATE utf8_unicode_ci NOT NULL,
  `checkString` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `callGroup_id_refs_id_6b1d7edf` (`callGroup_id`),
  KEY `oncallPerson_id_refs_id_b55a8f2` (`oncallPerson_id`),
  KEY `creator_id_refs_id_b55a8f2` (`creator_id`),
  CONSTRAINT `callGroup_id_refs_id_6b1d7edf` FOREIGN KEY (`callGroup_id`) REFERENCES `MHLCallGroups_callgroup` (`id`),
  CONSTRAINT `creator_id_refs_id_b55a8f2` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `oncallPerson_id_refs_id_b55a8f2` FOREIGN KEY (`oncallPerson_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Scheduler_evententry`
--

LOCK TABLES `Scheduler_evententry` WRITE;
/*!40000 ALTER TABLE `Scheduler_evententry` DISABLE KEYS */;
/*!40000 ALTER TABLE `Scheduler_evententry` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Validates_validation`
--

DROP TABLE IF EXISTS `Validates_validation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Validates_validation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(8) COLLATE utf8_unicode_ci NOT NULL,
  `type` int(11) DEFAULT NULL,
  `applicant` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `recipient` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `sent_time` datetime NOT NULL,
  `validate_locked_time` datetime DEFAULT NULL,
  `validate_success_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Validates_validation`
--

LOCK TABLES `Validates_validation` WRITE;
/*!40000 ALTER TABLE `Validates_validation` DISABLE KEYS */;
/*!40000 ALTER TABLE `Validates_validation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Validates_validationlog`
--

DROP TABLE IF EXISTS `Validates_validationlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Validates_validationlog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `validation_id` int(11) NOT NULL,
  `code_input` varchar(8) COLLATE utf8_unicode_ci NOT NULL,
  `validate_time` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `validation_id_refs_id_const` (`validation_id`),
  CONSTRAINT `validation_id_refs_id_const` FOREIGN KEY (`validation_id`) REFERENCES `Validates_validation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Validates_validationlog`
--

LOCK TABLES `Validates_validationlog` WRITE;
/*!40000 ALTER TABLE `Validates_validationlog` DISABLE KEYS */;
/*!40000 ALTER TABLE `Validates_validationlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `analytics_click2calldailysummary`
--

DROP TABLE IF EXISTS `analytics_click2calldailysummary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `analytics_click2calldailysummary` (
  `dateoflog` date NOT NULL,
  `countSuccess` int(11) NOT NULL,
  `countFailure` int(11) NOT NULL,
  `calcdate` datetime NOT NULL,
  PRIMARY KEY (`dateoflog`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `analytics_click2calldailysummary`
--

LOCK TABLES `analytics_click2calldailysummary` WRITE;
/*!40000 ALTER TABLE `analytics_click2calldailysummary` DISABLE KEYS */;
/*!40000 ALTER TABLE `analytics_click2calldailysummary` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `analytics_invitedailysummary`
--

DROP TABLE IF EXISTS `analytics_invitedailysummary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `analytics_invitedailysummary` (
  `dateoflog` date NOT NULL,
  `countTotal` int(11) NOT NULL,
  `countCanceled` int(11) NOT NULL,
  `calcdate` datetime NOT NULL,
  PRIMARY KEY (`dateoflog`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `analytics_invitedailysummary`
--

LOCK TABLES `analytics_invitedailysummary` WRITE;
/*!40000 ALTER TABLE `analytics_invitedailysummary` DISABLE KEYS */;
/*!40000 ALTER TABLE `analytics_invitedailysummary` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `analytics_messagedailysummary`
--

DROP TABLE IF EXISTS `analytics_messagedailysummary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `analytics_messagedailysummary` (
  `dateoflog` date NOT NULL,
  `countSuccess` int(11) NOT NULL,
  `countFailure` int(11) NOT NULL,
  `calcdate` datetime NOT NULL,
  PRIMARY KEY (`dateoflog`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `analytics_messagedailysummary`
--

LOCK TABLES `analytics_messagedailysummary` WRITE;
/*!40000 ALTER TABLE `analytics_messagedailysummary` DISABLE KEYS */;
/*!40000 ALTER TABLE `analytics_messagedailysummary` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `analytics_pagerdailysummary`
--

DROP TABLE IF EXISTS `analytics_pagerdailysummary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `analytics_pagerdailysummary` (
  `dateoflog` date NOT NULL,
  `countSuccess` int(11) NOT NULL,
  `calcdate` datetime NOT NULL,
  PRIMARY KEY (`dateoflog`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `analytics_pagerdailysummary`
--

LOCK TABLES `analytics_pagerdailysummary` WRITE;
/*!40000 ALTER TABLE `analytics_pagerdailysummary` DISABLE KEYS */;
/*!40000 ALTER TABLE `analytics_pagerdailysummary` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `analytics_salesleads`
--

DROP TABLE IF EXISTS `analytics_salesleads`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `analytics_salesleads` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `practice` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `status` varchar(12) COLLATE utf8_unicode_ci NOT NULL,
  `salestype` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `rep` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `contact` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `phone` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `email` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `website` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `date_contact` date NOT NULL,
  `date_appt` date NOT NULL,
  `price` decimal(20,2) NOT NULL,
  `interest` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `notes` longtext COLLATE utf8_unicode_ci NOT NULL,
  `address` longtext COLLATE utf8_unicode_ci NOT NULL,
  `region` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `analytics_salesleads`
--

LOCK TABLES `analytics_salesleads` WRITE;
/*!40000 ALTER TABLE `analytics_salesleads` DISABLE KEYS */;
/*!40000 ALTER TABLE `analytics_salesleads` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`,`permission_id`),
  KEY `permission_id_refs_id_4de83ca7792de1` (`permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_message`
--

DROP TABLE IF EXISTS `auth_message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_message` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `message` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auth_message_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_message`
--

LOCK TABLES `auth_message` WRITE;
/*!40000 ALTER TABLE `auth_message` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_message` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`codename`),
  KEY `auth_permission_content_type_id` (`content_type_id`)
) ENGINE=InnoDB AUTO_INCREMENT=283 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add permission',1,'add_permission'),(2,'Can change permission',1,'change_permission'),(3,'Can delete permission',1,'delete_permission'),(4,'Can add group',2,'add_group'),(5,'Can change group',2,'change_group'),(6,'Can delete group',2,'delete_group'),(7,'Can add user',3,'add_user'),(8,'Can change user',3,'change_user'),(9,'Can delete user',3,'delete_user'),(10,'Can add message',4,'add_message'),(11,'Can change message',4,'change_message'),(12,'Can delete message',4,'delete_message'),(13,'Can add content type',5,'add_contenttype'),(14,'Can change content type',5,'change_contenttype'),(15,'Can delete content type',5,'delete_contenttype'),(16,'Can add session',6,'add_session'),(17,'Can change session',6,'change_session'),(18,'Can delete session',6,'delete_session'),(19,'Can add site',7,'add_site'),(20,'Can change site',7,'change_site'),(21,'Can delete site',7,'delete_site'),(22,'Can add log entry',8,'add_logentry'),(23,'Can change log entry',8,'change_logentry'),(24,'Can delete log entry',8,'delete_logentry'),(25,'Can add message temp',9,'add_messagetemp'),(26,'Can change message temp',9,'change_messagetemp'),(27,'Can delete message temp',9,'delete_messagetemp'),(28,'Can add message log',10,'add_messagelog'),(29,'Can change message log',10,'change_messagelog'),(30,'Can delete message log',10,'delete_messagelog'),(31,'Can add click2 call_ log',11,'add_click2call_log'),(32,'Can change click2 call_ log',11,'change_click2call_log'),(33,'Can delete click2 call_ log',11,'delete_click2call_log'),(34,'Can add click2 call_ action log',12,'add_click2call_actionlog'),(35,'Can change click2 call_ action log',12,'change_click2call_actionlog'),(36,'Can delete click2 call_ action log',12,'delete_click2call_actionlog'),(37,'Can add pager log',13,'add_pagerlog'),(38,'Can change pager log',13,'change_pagerlog'),(39,'Can delete pager log',13,'delete_pagerlog'),(40,'Can add site analytics',14,'add_siteanalytics'),(41,'Can change site analytics',14,'change_siteanalytics'),(42,'Can delete site analytics',14,'delete_siteanalytics'),(43,'Can add vm message',15,'add_vmmessage'),(44,'Can change vm message',15,'change_vmmessage'),(45,'Can delete vm message',15,'delete_vmmessage'),(46,'Can add vm box_ config',16,'add_vmbox_config'),(47,'Can change vm box_ config',16,'change_vmbox_config'),(48,'Can delete vm box_ config',16,'delete_vmbox_config'),(49,'Can add call log',17,'add_calllog'),(50,'Can change call log',17,'change_calllog'),(51,'Can delete call log',17,'delete_calllog'),(52,'Can add call event',18,'add_callevent'),(53,'Can change call event',18,'change_callevent'),(54,'Can delete call event',18,'delete_callevent'),(55,'Can add call event target',19,'add_calleventtarget'),(56,'Can change call event target',19,'change_calleventtarget'),(57,'Can delete call event target',19,'delete_calleventtarget'),(58,'Can add ans svc dl failure',20,'add_anssvcdlfailure'),(59,'Can change ans svc dl failure',20,'change_anssvcdlfailure'),(60,'Can delete ans svc dl failure',20,'delete_anssvcdlfailure'),(61,'Can add ans svc dl failure activity log',21,'add_anssvcdlfailureactivitylog'),(62,'Can change ans svc dl failure activity log',21,'change_anssvcdlfailureactivitylog'),(63,'Can delete ans svc dl failure activity log',21,'delete_anssvcdlfailureactivitylog'),(64,'Can add message',22,'add_message'),(65,'Can change message',22,'change_message'),(66,'Can delete message',22,'delete_message'),(67,'Can add message recipient',23,'add_messagerecipient'),(68,'Can change message recipient',23,'change_messagerecipient'),(69,'Can delete message recipient',23,'delete_messagerecipient'),(70,'Can add message cc',24,'add_messagecc'),(71,'Can change message cc',24,'change_messagecc'),(72,'Can delete message cc',24,'delete_messagecc'),(73,'Can add message body user status',25,'add_messagebodyuserstatus'),(74,'Can change message body user status',25,'change_messagebodyuserstatus'),(75,'Can delete message body user status',25,'delete_messagebodyuserstatus'),(76,'Can add message body',26,'add_messagebody'),(77,'Can change message body',26,'c\nhange_messagebody'),(78,'Can delete message body',26,'delete_messagebody'),(79,'Can add message attachment',27,'add_messageattachment'),(80,'Can change message attachment',27,'change_messageattachment'),(81,'Can delete message attachment',27,'delete_messageattachment'),(82,'Can add callback log',28,'add_callbacklog'),(83,'Can change callback log',28,'change_callbacklog'),(84,'Can delete callback log',28,'delete_callbacklog'),(85,'Can add number pool',29,'add_numberpool'),(86,'Can change number pool',29,'change_numberpool'),(87,'Can delete number pool',29,'delete_numberpool'),(88,'Can add secure test message',30,'add_securetestmessage'),(89,'Can change secure test message',30,'change_securetestmessage'),(90,'Can delete secure test message',30,'delete_securetestmessage'),(91,'Can add private key',31,'add_privatekey'),(92,'Can change private key',31,'change_privatekey'),(93,'Can delete private key',31,'delete_privatekey'),(94,'Can add iv r_ private key',32,'add_ivr_privatekey'),(95,'Can change iv r_ private key',32,'change_ivr_privatekey'),(96,'Can delete iv r_ private key',32,'delete_ivr_privatekey'),(97,'Can add admin private key',33,'add_adminprivatekey'),(98,'Can change admin private key',33,'change_adminprivatekey'),(99,'Can delete admin private key',33,'delete_adminprivatekey'),(100,'Can add rsa pub key',34,'add_rsapubkey'),(101,'Can change rsa pub key',34,'change_rsapubkey'),(102,'Can delete rsa pub key',34,'delete_rsapubkey'),(103,'Can add iv r_rsa pub key',35,'add_ivr_rsapubkey'),(104,'Can change iv r_rsa pub key',35,'change_ivr_rsapubkey'),(105,'Can delete iv r_rsa pub key',35,'delete_ivr_rsapubkey'),(106,'Can add rsa key pair',36,'add_rsakeypair'),(107,'Can change rsa key pair',36,'change_rsakeypair'),(108,'Can delete rsa key pair',36,'delete_rsakeypair'),(109,'Can add iv r_rsa key pair',37,'add_ivr_rsakeypair'),(110,'Can change iv r_rsa key pair',37,'change_ivr_rsakeypair'),(111,'Can delete iv r_rsa key pair',37,'delete_ivr_rsakeypair'),(112,'Can add login event',38,'add_loginevent'),(113,'Can change login event',38,'change_loginevent'),(114,'Can delete login event',38,'delete_loginevent'),(115,'Can add logout event',39,'add_logoutevent'),(116,'Can change logout event',39,'change_logoutevent'),(117,'Can delete logout event',39,'delete_logoutevent'),(118,'Can add practice location',40,'add_practicelocation'),(119,'Can change practice location',40,'change_practicelocation'),(120,'Can delete practice location',40,'delete_practicelocation'),(121,'Can add practice group',41,'add_practicegroup'),(122,'Can change practice group',41,'change_practicegroup'),(123,'Can delete practice group',41,'delete_practicegroup'),(124,'Can add practice hours',42,'add_practicehours'),(125,'Can change practice hours',42,'change_practicehours'),(126,'Can delete practice hours',42,'delete_practicehours'),(127,'Can add practice holidays',43,'add_practiceholidays'),(128,'Can change practice holidays',43,'change_practiceholidays'),(129,'Can delete practice holidays',43,'delete_practiceholidays'),(130,'Can add pending_ association',44,'add_pending_association'),(131,'Can change pending_ association',44,'change_pending_association'),(132,'Can delete pending_ association',44,'delete_pending_association'),(133,'Can add log_ association',45,'add_log_association'),(134,'Can change log_ association',45,'change_log_association'),(135,'Can delete log_ association',45,'delete_log_association'),(136,'Can add access number',46,'add_accessnumber'),(137,'Can change access number',46,'change_accessnumber'),(138,'Can delete access number',46,'delete_accessnumber'),(139,'Can add site',47,'add_site'),(140,'Can change site',47,'change_site'),(141,'Can delete site',47,'delete_site'),(142,'Can add hospital',48,'add_hospital'),(143,'Can change hospital',48,'change_hospital'),(144,'Can delete hospital',48,'delete_hospital'),(145,'Can add states',49,'add_states'),(146,'Can change states',49,'change_states'),(147,'Can delete states',49,'delete_states'),(148,'Can add mhl user',50,'add_mhluser'),(149,'Can change mhl user',50,'change_mhluser'),(150,'Can delete mhl user\n',50,'delete_mhluser'),(151,'Can add user profile',51,'add_userprofile'),(152,'Can change user profile',51,'change_userprofile'),(153,'Can delete user profile',51,'delete_userprofile'),(154,'Can add provider',52,'add_provider'),(155,'Can change provider',52,'change_provider'),(156,'Can delete provider',52,'delete_provider'),(157,'Can add Office Staff',53,'add_officestaff'),(158,'Can change Office Staff',53,'change_officestaff'),(159,'Can delete Office Staff',53,'delete_officestaff'),(160,'Can add physician',54,'add_physician'),(161,'Can change physician',54,'change_physician'),(162,'Can delete physician',54,'delete_physician'),(163,'Can add NP/PA',55,'add_np_pa'),(164,'Can change NP/PA',55,'change_np_pa'),(165,'Can delete NP/PA',55,'delete_np_pa'),(166,'Can add nurse',56,'add_nurse'),(167,'Can change nurse',56,'change_nurse'),(168,'Can delete nurse',56,'delete_nurse'),(169,'Can add Office Manager',57,'add_office_manager'),(170,'Can change Office Manager',57,'change_office_manager'),(171,'Can delete Office Manager',57,'delete_office_manager'),(172,'Can add dietician',58,'add_dietician'),(173,'Can change dietician',58,'change_dietician'),(174,'Can delete dietician',58,'delete_dietician'),(175,'Can add System Administrator',59,'add_administrator'),(176,'Can change System Administrator',59,'change_administrator'),(177,'Can delete System Administrator',59,'delete_administrator'),(178,'Can add password reset log',60,'add_passwordresetlog'),(179,'Can change password reset log',60,'change_passwordresetlog'),(180,'Can delete password reset log',60,'delete_passwordresetlog'),(181,'Can add patient',61,'add_patient'),(182,'Can change patient',61,'change_patient'),(183,'Can delete patient',61,'delete_patient'),(184,'Can add physician group',62,'add_physiciangroup'),(185,'Can change physician group',62,'change_physiciangroup'),(186,'Can delete physician group',62,'delete_physiciangroup'),(187,'Can add physician group members',63,'add_physiciangroupmembers'),(188,'Can change physician group members',63,'change_physiciangroupmembers'),(189,'Can delete physician group members',63,'delete_physiciangroupmembers'),(190,'Can add event log',64,'add_eventlog'),(191,'Can change event log',64,'change_eventlog'),(192,'Can delete event log',64,'delete_eventlog'),(193,'Can add security questions',65,'add_securityquestions'),(194,'Can change security questions',65,'change_securityquestions'),(195,'Can delete security questions',65,'delete_securityquestions'),(196,'Can add Salesperson',66,'add_salesperson'),(197,'Can change Salesperson',66,'change_salesperson'),(198,'Can delete Salesperson',66,'delete_salesperson'),(199,'Can add invitation',67,'add_invitation'),(200,'Can change invitation',67,'change_invitation'),(201,'Can delete invitation',67,'delete_invitation'),(202,'Can add invitation log',68,'add_invitationlog'),(203,'Can change invitation log',68,'change_invitationlog'),(204,'Can delete invitation log',68,'delete_invitationlog'),(205,'Can add contact',69,'add_contact'),(206,'Can change contact',69,'change_contact'),(207,'Can delete contact',69,'delete_contact'),(208,'Can add forgot password',70,'add_forgotpassword'),(209,'Can change forgot password',70,'change_forgotpassword'),(210,'Can delete forgot password',70,'delete_forgotpassword'),(211,'Can add twilio call gather test',71,'add_twiliocallgathertest'),(212,'Can change twilio call gather test',71,'change_twiliocallgathertest'),(213,'Can delete twilio call gather test',71,'delete_twiliocallgathertest'),(214,'Can add twilio record test',72,'add_twiliorecordtest'),(215,'Can change twilio record test',72,'change_twiliorecordtest'),(216,'Can delete twilio record test',72,'delete_twiliorecordtest'),(217,'Can add convergent test',73,'add_convergenttest'),(218,'Can change convergent test',73,'change_convergenttest'),(219,'Can delete convergent test',73,'delete_convergenttest'),(220,'Can add doctor com c2c test',74,'add_doctorcomc2ctest'),(221,'Can change doctor com c2c test',74,'change_doctorcomc2ctest'),(222,'Can delete doctor com c2c test',74,'delete_doctorcomc2ctest'),(223,'Can add doctor com p\nager test',75,'add_doctorcompagertest'),(224,'Can change doctor com pager test',75,'change_doctorcompagertest'),(225,'Can delete doctor com pager test',75,'delete_doctorcompagertest'),(226,'Can add doctor com sms test',76,'add_doctorcomsmstest'),(227,'Can change doctor com sms test',76,'change_doctorcomsmstest'),(228,'Can delete doctor com sms test',76,'delete_doctorcomsmstest'),(229,'Can add smart phone assn',77,'add_smartphoneassn'),(230,'Can change smart phone assn',77,'change_smartphoneassn'),(231,'Can delete smart phone assn',77,'delete_smartphoneassn'),(232,'Can add smart phone assn log',78,'add_smartphoneassnlog'),(233,'Can change smart phone assn log',78,'change_smartphoneassnlog'),(234,'Can delete smart phone assn log',78,'delete_smartphoneassnlog'),(235,'Can add billing account',79,'add_billingaccount'),(236,'Can change billing account',79,'change_billingaccount'),(237,'Can delete billing account',79,'delete_billingaccount'),(238,'Can add minutes product',80,'add_minutesproduct'),(239,'Can change minutes product',80,'change_minutesproduct'),(240,'Can delete minutes product',80,'delete_minutesproduct'),(241,'Can add billing funds bucket',81,'add_billingfundsbucket'),(242,'Can change billing funds bucket',81,'change_billingfundsbucket'),(243,'Can delete billing funds bucket',81,'delete_billingfundsbucket'),(244,'Can add billing transaction',82,'add_billingtransaction'),(245,'Can change billing transaction',82,'change_billingtransaction'),(246,'Can delete billing transaction',82,'delete_billingtransaction'),(247,'Can add sender lookup',83,'add_senderlookup'),(248,'Can change sender lookup',83,'change_senderlookup'),(249,'Can delete sender lookup',83,'delete_senderlookup'),(250,'Can add follow ups',84,'add_followups'),(251,'Can change follow ups',84,'change_followups'),(252,'Can delete follow ups',84,'delete_followups'),(253,'Can add pager daily summary',85,'add_pagerdailysummary'),(254,'Can change pager daily summary',85,'change_pagerdailysummary'),(255,'Can delete pager daily summary',85,'delete_pagerdailysummary'),(256,'Can add click2 call daily summary',86,'add_click2calldailysummary'),(257,'Can change click2 call daily summary',86,'change_click2calldailysummary'),(258,'Can delete click2 call daily summary',86,'delete_click2calldailysummary'),(259,'Can add message daily summary',87,'add_messagedailysummary'),(260,'Can change message daily summary',87,'change_messagedailysummary'),(261,'Can delete message daily summary',87,'delete_messagedailysummary'),(262,'Can add invite daily summary',88,'add_invitedailysummary'),(263,'Can change invite daily summary',88,'change_invitedailysummary'),(264,'Can delete invite daily summary',88,'delete_invitedailysummary'),(265,'Can add call group',89,'add_callgroup'),(266,'Can change call group',89,'change_callgroup'),(267,'Can delete call group',89,'delete_callgroup'),(268,'Can add Call Group Member',90,'add_callgroupmember'),(269,'Can change Call Group Member',90,'change_callgroupmember'),(270,'Can delete Call Group Member',90,'delete_callgroupmember'),(271,'Can add event entry',91,'add_evententry'),(272,'Can change event entry',91,'change_evententry'),(273,'Can delete event entry',91,'delete_evententry'),(274,'Can add corp',92,'add_corp'),(275,'Can change corp',92,'change_corp'),(276,'Can delete corp',92,'delete_corp'),(277,'Can add press release',93,'add_pressrelease'),(278,'Can change press release',93,'change_pressrelease'),(279,'Can delete press release',93,'delete_pressrelease'),(280,'Can add our team',94,'add_ourteam'),(281,'Can change our team',94,'change_ourteam'),(282,'Can delete our team',94,'delete_ourteam');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `first_name` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `last_name` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `email` varchar(75) COLLATE utf8_unicode_ci NOT NULL,
  `password` varchar(128) COLLATE utf8_unicode_ci NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `last_login` datetime NOT NULL,
  `date_joined` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'admin','Tony','Yin','jyi1n@suzhoukada.com','sha1$5b287$60ca3a51a6c9a862398b1f132c21f8beee98b16b',1,1,1,'2013-03-05 20:41:37','2012-04-23 20:51:32'),(2,'practicemgr','Practice','Manager1','mwang@suzhoukada.com','sha1$106be$1c66192d9532ee5615934eb7b164c909ee9982b1',0,1,0,'2013-03-05 20:55:45','2013-03-05 20:55:30');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`group_id`),
  KEY `group_id_refs_id_321a8efef0ee9890` (`group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`permission_id`),
  KEY `permission_id_refs_id_6d7fb3c2067e79cb` (`permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `contactme_contact`
--

DROP TABLE IF EXISTS `contactme_contact`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `contactme_contact` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `first_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `last_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `company_name` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `email` varchar(75) COLLATE utf8_unicode_ci NOT NULL,
  `phone` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `msg` longtext COLLATE utf8_unicode_ci,
  `ip_address` char(15) COLLATE utf8_unicode_ci NOT NULL,
  `date` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contactme_contact`
--

LOCK TABLES `contactme_contact` WRITE;
/*!40000 ALTER TABLE `contactme_contact` DISABLE KEYS */;
/*!40000 ALTER TABLE `contactme_contact` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `contactme_forgotpassword`
--

DROP TABLE IF EXISTS `contactme_forgotpassword`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `contactme_forgotpassword` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `first_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `last_name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `company_name` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `email` varchar(75) COLLATE utf8_unicode_ci NOT NULL,
  `phone` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL,
  `msg` longtext COLLATE utf8_unicode_ci,
  `ip_address` char(15) COLLATE utf8_unicode_ci NOT NULL,
  `date` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contactme_forgotpassword`
--

LOCK TABLES `contactme_forgotpassword` WRITE;
/*!40000 ALTER TABLE `contactme_forgotpassword` DISABLE KEYS */;
/*!40000 ALTER TABLE `contactme_forgotpassword` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime NOT NULL,
  `user_id` int(11) NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `object_id` longtext COLLATE utf8_unicode_ci,
  `object_repr` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_user_id` (`user_id`),
  KEY `django_admin_log_content_type_id` (`content_type_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2013-03-05 20:58:52',1,52,'1','Tony Yin',2,'lat, longit, office_lat, office_longit, current_practice und practices geändert.');
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_braintree_paymentlog`
--

DROP TABLE IF EXISTS `django_braintree_paymentlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_braintree_paymentlog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `amount` decimal(7,2) NOT NULL,
  `timestamp` datetime NOT NULL,
  `transaction_id` varchar(128) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id_refs_id_354c4cc` (`user_id`),
  CONSTRAINT `user_id_refs_id_354c4cc` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_braintree_paymentlog`
--

LOCK TABLES `django_braintree_paymentlog` WRITE;
/*!40000 ALTER TABLE `django_braintree_paymentlog` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_braintree_paymentlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_braintree_uservault`
--

DROP TABLE IF EXISTS `django_braintree_uservault`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_braintree_uservault` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `vault_id` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `vault_id` (`vault_id`),
  CONSTRAINT `user_id_refs_id_2fb69280` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_braintree_uservault`
--

LOCK TABLES `django_braintree_uservault` WRITE;
/*!40000 ALTER TABLE `django_braintree_uservault` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_braintree_uservault` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `app_label` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `model` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `app_label` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=97 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'permission','auth','permission'),(2,'group','auth','group'),(3,'user','auth','user'),(4,'message','auth','message'),(5,'content type','contenttypes','contenttype'),(6,'session','sessions','session'),(7,'site','sites','site'),(8,'log entry','admin','logentry'),(9,'message temp','DoctorCom','messagetemp'),(10,'message log','DoctorCom','messagelog'),(11,'click2 call_ log','DoctorCom','click2call_log'),(12,'click2 call_ action log','DoctorCom','click2call_actionlog'),(13,'pager log','DoctorCom','pagerlog'),(14,'site analytics','DoctorCom','siteanalytics'),(15,'vm message','IVR','vmmessage'),(16,'vm box_ config','IVR','vmbox_config'),(17,'call log','IVR','calllog'),(18,'call event','IVR','callevent'),(19,'call event target','IVR','calleventtarget'),(20,'ans svc dl failure','IVR','anssvcdlfailure'),(21,'ans svc dl failure activity log','IVR','anssvcdlfailureactivitylog'),(22,'message','Messaging','message'),(23,'message recipient','Messaging','messagerecipient'),(24,'message cc','Messaging','messagecc'),(25,'message body user status','Messaging','messagebodyuserstatus'),(26,'message body','Messaging','messagebody'),(27,'message attachment','Messaging','messageattachment'),(28,'callback log','Messaging','callbacklog'),(29,'number pool','NumberProvisioner','numberpool'),(30,'secure test message','KMS','securetestmessage'),(31,'private key','KMS','privatekey'),(32,'iv r_ private key','KMS','ivr_privatekey'),(33,'admin private key','KMS','adminprivatekey'),(34,'rsa pub key','KMS','rsapubkey'),(35,'iv r_rsa pub key','KMS','ivr_rsapubkey'),(36,'rsa key pair','KMS','rsakeypair'),(37,'iv r_rsa key pair','KMS','ivr_rsakeypair'),(38,'login event','Logs','loginevent'),(39,'logout event','Logs','logoutevent'),(40,'practice location','MHLPractices','practicelocation'),(41,'practice group','MHLPractices','practicegroup'),(42,'practice hours','MHLPractices','practicehours'),(43,'practice holidays','MHLPractices','practiceholidays'),(44,'pending_ association','MHLPractices','pending_association'),(45,'log_ association','MHLPractices','log_association'),(46,'access number','MHLPractices','accessnumber'),(47,'site','MHLSites','site'),(48,'hospital','MHLSites','hospital'),(49,'states','MHLUsers','states'),(50,'mhl user','MHLUsers','mhluser'),(51,'user profile','MHLUsers','userprofile'),(52,'provider','MHLUsers','provider'),(53,'Office Staff','MHLUsers','officestaff'),(54,'physician','MHLUsers','physician'),(55,'NP/PA','MHLUsers','np_pa'),(56,'nurse','MHLUsers','nurse'),(57,'Office Manager','MHLUsers','office_manager'),(58,'dietician','MHLUsers','dietician'),(59,'System Administrator','MHLUsers','administrator'),(60,'password reset log','MHLUsers','passwordresetlog'),(61,'patient','MHLUsers','patient'),(62,'physician group','MHLUsers','physiciangroup'),(63,'physician group members','MHLUsers','physiciangroupmembers'),(64,'event log','MHLUsers','eventlog'),(65,'security questions','MHLUsers','securityquestions'),(66,'Salesperson','Sales','salesperson'),(67,'invitation','Invites','invitation'),(68,'invitation log','Invites','invitationlog'),(69,'contact','contactme','contact'),(70,'forgot password','contactme','forgotpassword'),(71,'twilio call gather test','tests','twiliocallgathertest'),(72,'twilio record test','tests','twiliorecordtest'),(73,'convergent test','tests','convergenttest'),(74,'doctor com c2c test','tests','doctorcomc2ctest'),(75,'doctor com pager test','tests','doctorcompagertest'),(76,'doctor com sms test','tests','doctorcomsmstest'),(77,'smart phone assn','smartphone','smartphoneassn'),(78,'smart phone assn log','smartphone','smartphoneassnlog'),(79,'billing account','Billing','billingaccount'),(80,'minutes product','Billing','minutesproduct'),(81,'billing funds bucket','Billing','billingfundsbucket'),(82,'billing transaction','Billing','billingtransaction'),(83,'sender lookup','SMS','senderlookup'),(84,'follow ups','followup','followups'),(85,'pager daily summary','analytics','pagerdailysummary'),(86,'click2 call daily summary','analytics','click2calldailysummary'),(87,'message daily s\nummary','analytics','messagedailysummary'),(88,'invite daily summary','analytics','invitedailysummary'),(89,'call group','MHLCallGroups','callgroup'),(90,'Call Group Member','MHLCallGroups','callgroupmember'),(91,'event entry','Scheduler','evententry'),(92,'corp','corp','corp'),(93,'press release','corp','pressrelease'),(94,'our team','corp','ourteam'),(95,'message refer','Messaging','messagerefer'),(96,'broker','MHLUsers','broker');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) COLLATE utf8_unicode_ci NOT NULL,
  `session_data` longtext COLLATE utf8_unicode_ci NOT NULL,
  `expire_date` datetime NOT NULL,
  PRIMARY KEY (`session_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_site`
--

DROP TABLE IF EXISTS `django_site`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_site` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `domain` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_site`
--

LOCK TABLES `django_site` WRITE;
/*!40000 ALTER TABLE `django_site` DISABLE KEYS */;
INSERT INTO `django_site` VALUES (1,'de.mdcom.com','de.mdcom.com');
/*!40000 ALTER TABLE `django_site` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `doctorcom_click2call_actionlog`
--

DROP TABLE IF EXISTS `doctorcom_click2call_actionlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `doctorcom_click2call_actionlog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `click2call_log_id` int(11) NOT NULL,
  `action` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `click2call_log_id_refs_id_7e052c49` (`click2call_log_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `doctorcom_click2call_actionlog`
--

LOCK TABLES `doctorcom_click2call_actionlog` WRITE;
/*!40000 ALTER TABLE `doctorcom_click2call_actionlog` DISABLE KEYS */;
/*!40000 ALTER TABLE `doctorcom_click2call_actionlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `followup_followups`
--

DROP TABLE IF EXISTS `followup_followups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `followup_followups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `done` tinyint(1) NOT NULL,
  `priority` int(11) NOT NULL,
  `task` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `creation_date` datetime NOT NULL,
  `due_date` datetime DEFAULT NULL,
  `completion_date` datetime DEFAULT NULL,
  `deleted` tinyint(1) NOT NULL,
  `note` longtext COLLATE utf8_unicode_ci,
  `content_type_id` int(11) DEFAULT NULL,
  `object_id` int(10) unsigned DEFAULT NULL,
  `update_timestamp` datetime NOT NULL DEFAULT '1970-01-01 00:00:00',
  PRIMARY KEY (`id`),
  KEY `followup_followups_user_id` (`user_id`),
  KEY `followup_followups_content_type_id` (`content_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `followup_followups`
--

LOCK TABLES `followup_followups` WRITE;
/*!40000 ALTER TABLE `followup_followups` DISABLE KEYS */;
/*!40000 ALTER TABLE `followup_followups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `genbilling_account`
--

DROP TABLE IF EXISTS `genbilling_account`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `genbilling_account` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `account_no` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `practice_group_id` int(11) DEFAULT NULL,
  `owner_id` int(11) NOT NULL,
  `status` varchar(1) COLLATE utf8_unicode_ci NOT NULL,
  `last_bill_date` datetime DEFAULT NULL,
  `last_payment_state` varchar(1) COLLATE utf8_unicode_ci NOT NULL,
  `created_on` datetime NOT NULL,
  `last_modified` datetime NOT NULL,
  `practice_group_new_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `account_no` (`account_no`),
  UNIQUE KEY `owner_id` (`owner_id`),
  UNIQUE KEY `practice_group_id` (`practice_group_id`),
  UNIQUE KEY `practice_group_new_id` (`practice_group_new_id`),
  CONSTRAINT `owner_id_refs_id_fc9e2ad` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `practice_group_id_refs_id_17738634` FOREIGN KEY (`practice_group_id`) REFERENCES `MHLPractices_practicegroup` (`id`),
  CONSTRAINT `practice_group_new_id_refs_id_081b30fc` FOREIGN KEY (`practice_group_new_id`) REFERENCES `MHLPractices_practicelocation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `genbilling_account`
--

LOCK TABLES `genbilling_account` WRITE;
/*!40000 ALTER TABLE `genbilling_account` DISABLE KEYS */;
/*!40000 ALTER TABLE `genbilling_account` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `genbilling_accounttransaction`
--

DROP TABLE IF EXISTS `genbilling_accounttransaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `genbilling_accounttransaction` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `account_id` int(11) NOT NULL,
  `reference_no` varchar(36) COLLATE utf8_unicode_ci NOT NULL,
  `tx_type` varchar(3) COLLATE utf8_unicode_ci NOT NULL,
  `amount` decimal(8,2) NOT NULL,
  `created_on` datetime NOT NULL,
  `period_start` int(11) NOT NULL,
  `period_end` int(11) NOT NULL,
  `memo` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `reference_no` (`reference_no`),
  KEY `genbilling_accounttransaction_6f2fe10e` (`account_id`),
  CONSTRAINT `account_id_refs_id_3ce922f0` FOREIGN KEY (`account_id`) REFERENCES `genbilling_account` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `genbilling_accounttransaction`
--

LOCK TABLES `genbilling_accounttransaction` WRITE;
/*!40000 ALTER TABLE `genbilling_accounttransaction` DISABLE KEYS */;
/*!40000 ALTER TABLE `genbilling_accounttransaction` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `genbilling_failedtransaction`
--

DROP TABLE IF EXISTS `genbilling_failedtransaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `genbilling_failedtransaction` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `accounttransaction_id` int(11) NOT NULL,
  `response_code` int(11) NOT NULL,
  `message` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `genbilling_failedtransaction_4db48d0b` (`accounttransaction_id`),
  CONSTRAINT `accounttransaction_id_refs_id_393839f4` FOREIGN KEY (`accounttransaction_id`) REFERENCES `genbilling_accounttransaction` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `genbilling_failedtransaction`
--

LOCK TABLES `genbilling_failedtransaction` WRITE;
/*!40000 ALTER TABLE `genbilling_failedtransaction` DISABLE KEYS */;
/*!40000 ALTER TABLE `genbilling_failedtransaction` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `genbilling_invoice`
--

DROP TABLE IF EXISTS `genbilling_invoice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `genbilling_invoice` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `accounttransaction_id` int(11) NOT NULL,
  `paid` tinyint(1) NOT NULL,
  `failed` tinyint(1) NOT NULL,
  `paymentlog_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounttransaction_id` (`accounttransaction_id`),
  UNIQUE KEY `paymentlog_id` (`paymentlog_id`),
  CONSTRAINT `accounttransaction_id_refs_id_2e3b5bc2` FOREIGN KEY (`accounttransaction_id`) REFERENCES `genbilling_accounttransaction` (`id`),
  CONSTRAINT `paymentlog_id_refs_id_2f9f07e6` FOREIGN KEY (`paymentlog_id`) REFERENCES `django_braintree_paymentlog` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `genbilling_invoice`
--

LOCK TABLES `genbilling_invoice` WRITE;
/*!40000 ALTER TABLE `genbilling_invoice` DISABLE KEYS */;
/*!40000 ALTER TABLE `genbilling_invoice` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `genbilling_subscription`
--

DROP TABLE IF EXISTS `genbilling_subscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `genbilling_subscription` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `practice_group_id` int(11) DEFAULT NULL,
  `product_id` int(11) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `price` decimal(20,2) NOT NULL,
  `start_date` datetime DEFAULT NULL,
  `created_on` datetime NOT NULL,
  `last_modified` datetime NOT NULL,
  `practice_location_id` int(11) DEFAULT NULL,
  `practice_group_new_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `genbilling_subscription_1cf897ed` (`practice_group_id`),
  KEY `genbilling_subscription_44bdf3ee` (`product_id`),
  KEY `genbilling_subscription_366c0f3e` (`practice_location_id`),
  KEY `practice_group_new_id_refs_id_da5b35d9` (`practice_group_new_id`),
  CONSTRAINT `practice_group_new_id_refs_id_da5b35d9` FOREIGN KEY (`practice_group_new_id`) REFERENCES `MHLPractices_practicelocation` (`id`),
  CONSTRAINT `practice_location_id_refs_id_3f99c184` FOREIGN KEY (`practice_location_id`) REFERENCES `MHLPractices_practicelocation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `genbilling_subscription`
--

LOCK TABLES `genbilling_subscription` WRITE;
/*!40000 ALTER TABLE `genbilling_subscription` DISABLE KEYS */;
/*!40000 ALTER TABLE `genbilling_subscription` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `logtailer_filter`
--

DROP TABLE IF EXISTS `logtailer_filter`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logtailer_filter` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(180) COLLATE utf8_unicode_ci NOT NULL,
  `regex` varchar(500) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `logtailer_filter`
--

LOCK TABLES `logtailer_filter` WRITE;
/*!40000 ALTER TABLE `logtailer_filter` DISABLE KEYS */;
/*!40000 ALTER TABLE `logtailer_filter` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `logtailer_logfile`
--

DROP TABLE IF EXISTS `logtailer_logfile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logtailer_logfile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(180) COLLATE utf8_unicode_ci NOT NULL,
  `path` varchar(500) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `logtailer_logfile`
--

LOCK TABLES `logtailer_logfile` WRITE;
/*!40000 ALTER TABLE `logtailer_logfile` DISABLE KEYS */;
INSERT INTO `logtailer_logfile` VALUES (1,'geocode','/workspace/mdcom/MHLogin/logfiles/utils/geocode.log');
/*!40000 ALTER TABLE `logtailer_logfile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `logtailer_logsclipboard`
--

DROP TABLE IF EXISTS `logtailer_logsclipboard`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logtailer_logsclipboard` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(180) COLLATE utf8_unicode_ci NOT NULL,
  `notes` longtext COLLATE utf8_unicode_ci,
  `logs` longtext COLLATE utf8_unicode_ci NOT NULL,
  `log_file_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `logtailer_logsclipboard_29dd0a2d` (`log_file_id`),
  CONSTRAINT `log_file_id_refs_id_af50890a` FOREIGN KEY (`log_file_id`) REFERENCES `logtailer_logfile` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `logtailer_logsclipboard`
--

LOCK TABLES `logtailer_logsclipboard` WRITE;
/*!40000 ALTER TABLE `logtailer_logsclipboard` DISABLE KEYS */;
/*!40000 ALTER TABLE `logtailer_logsclipboard` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `remotelog_application`
--

DROP TABLE IF EXISTS `remotelog_application`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `remotelog_application` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `slug` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `remotelog_application_a951d5d6` (`slug`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `remotelog_application`
--

LOCK TABLES `remotelog_application` WRITE;
/*!40000 ALTER TABLE `remotelog_application` DISABLE KEYS */;
INSERT INTO `remotelog_application` VALUES (1,'analytics','analytics'),(2,'geocode','geocode');
/*!40000 ALTER TABLE `remotelog_application` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `remotelog_logmessage`
--

DROP TABLE IF EXISTS `remotelog_logmessage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `remotelog_logmessage` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `application_id` int(11) NOT NULL,
  `date` datetime NOT NULL,
  `remote_ip` varchar(40) COLLATE utf8_unicode_ci NOT NULL,
  `remote_host` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `levelno` int(11) NOT NULL,
  `levelname` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `module` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `filename` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `pathname` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `funcName` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `lineno` int(11) NOT NULL,
  `msg` longtext COLLATE utf8_unicode_ci NOT NULL,
  `exc_info` longtext COLLATE utf8_unicode_ci,
  `exc_text` longtext COLLATE utf8_unicode_ci,
  `args` longtext COLLATE utf8_unicode_ci,
  `threadName` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `thread` double NOT NULL,
  `created` double NOT NULL,
  `process` int(11) NOT NULL,
  `relativeCreated` double NOT NULL,
  `msecs` double NOT NULL,
  PRIMARY KEY (`id`),
  KEY `remotelog_logmessage_398529ef` (`application_id`),
  CONSTRAINT `application_id_refs_id_12f0475f` FOREIGN KEY (`application_id`) REFERENCES `remotelog_application` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `remotelog_logmessage`
--

LOCK TABLES `remotelog_logmessage` WRITE;
/*!40000 ALTER TABLE `remotelog_logmessage` DISABLE KEYS */;
/*!40000 ALTER TABLE `remotelog_logmessage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `smartphone_smartphoneassn`
--

DROP TABLE IF EXISTS `smartphone_smartphoneassn`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `smartphone_smartphoneassn` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `device_id` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `device_serial` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `user_id` int(11) NOT NULL,
  `name` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `version` varchar(32) COLLATE utf8_unicode_ci DEFAULT NULL,
  `platform` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `secret` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `secret_hash` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `password_reset` tinyint(1) NOT NULL,
  `db_secret` longtext COLLATE utf8_unicode_ci,
  `db_hash` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `push_token` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `user_type` int(11) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `device_id` (`device_id`),
  KEY `user_id_refs_user_ptr_id_577fbcca` (`user_id`),
  CONSTRAINT `user_id_refs_user_ptr_id_577fbcca` FOREIGN KEY (`user_id`) REFERENCES `MHLUsers_mhluser` (`user_ptr_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `smartphone_smartphoneassn`
--

LOCK TABLES `smartphone_smartphoneassn` WRITE;
/*!40000 ALTER TABLE `smartphone_smartphoneassn` DISABLE KEYS */;
/*!40000 ALTER TABLE `smartphone_smartphoneassn` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `smartphone_smartphoneassnlog`
--

DROP TABLE IF EXISTS `smartphone_smartphoneassnlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `smartphone_smartphoneassnlog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `device_id` varchar(32) COLLATE utf8_unicode_ci NOT NULL,
  `serial` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `requesting_ip` char(15) COLLATE utf8_unicode_ci NOT NULL,
  `timestamp` datetime NOT NULL,
  `action` varchar(3) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `smartphone_smartphoneassnlog`
--

LOCK TABLES `smartphone_smartphoneassnlog` WRITE;
/*!40000 ALTER TABLE `smartphone_smartphoneassnlog` DISABLE KEYS */;
/*!40000 ALTER TABLE `smartphone_smartphoneassnlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `speech_neospeechconfig`
--

DROP TABLE IF EXISTS `speech_neospeechconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `speech_neospeechconfig` (
  `speechconfig_ptr_id` int(11) NOT NULL,
  `server` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `server_port` int(10) unsigned NOT NULL,
  `status_port` int(10) unsigned NOT NULL,
  `admin_port` int(10) unsigned NOT NULL,
  `voice_id` int(11) NOT NULL,
  `encoding` int(11) NOT NULL,
  `volume` int(10) unsigned NOT NULL DEFAULT '100',
  `speed` int(10) unsigned NOT NULL DEFAULT '100',
  `pitch` int(10) unsigned NOT NULL DEFAULT '100',
  PRIMARY KEY (`speechconfig_ptr_id`),
  CONSTRAINT `speechconfig_ptr_id_refs_id_d76601be` FOREIGN KEY (`speechconfig_ptr_id`) REFERENCES `speech_speechconfig` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `speech_neospeechconfig`
--

LOCK TABLES `speech_neospeechconfig` WRITE;
/*!40000 ALTER TABLE `speech_neospeechconfig` DISABLE KEYS */;
/*!40000 ALTER TABLE `speech_neospeechconfig` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `speech_speechconfig`
--

DROP TABLE IF EXISTS `speech_speechconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `speech_speechconfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `spoken_lang` varchar(16) COLLATE utf8_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `speech_speechconfig`
--

LOCK TABLES `speech_speechconfig` WRITE;
/*!40000 ALTER TABLE `speech_speechconfig` DISABLE KEYS */;
/*!40000 ALTER TABLE `speech_speechconfig` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `speech_voiceclip`
--

DROP TABLE IF EXISTS `speech_voiceclip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `speech_voiceclip` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `config_id` int(11) NOT NULL,
  `filename` varchar(128) COLLATE utf8_unicode_ci NOT NULL,
  `checksum` varchar(128) COLLATE utf8_unicode_ci NOT NULL,
  `spoken_text` longtext COLLATE utf8_unicode_ci NOT NULL,
  `access_count` int(10) unsigned NOT NULL,
  `access_date` datetime NOT NULL,
  `create_date` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `config_id_refs_id_b570042e` (`config_id`),
  CONSTRAINT `config_id_refs_id_b570042e` FOREIGN KEY (`config_id`) REFERENCES `speech_speechconfig` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `speech_voiceclip`
--

LOCK TABLES `speech_voiceclip` WRITE;
/*!40000 ALTER TABLE `speech_voiceclip` DISABLE KEYS */;
/*!40000 ALTER TABLE `speech_voiceclip` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tests_convergenttest`
--

DROP TABLE IF EXISTS `tests_convergenttest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tests_convergenttest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tester_id` int(11) NOT NULL,
  `message` longtext COLLATE utf8_unicode_ci NOT NULL,
  `confirmations` varchar(250) COLLATE utf8_unicode_ci NOT NULL,
  `success` int(11) NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tests_convergenttest_tester_id` (`tester_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tests_convergenttest`
--

LOCK TABLES `tests_convergenttest` WRITE;
/*!40000 ALTER TABLE `tests_convergenttest` DISABLE KEYS */;
/*!40000 ALTER TABLE `tests_convergenttest` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tests_doctorcomc2ctest`
--

DROP TABLE IF EXISTS `tests_doctorcomc2ctest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tests_doctorcomc2ctest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tester_id` int(11) NOT NULL,
  `call_id` int(11) DEFAULT NULL,
  `success` int(11) NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tests_doctorcomc2ctest_tester_id` (`tester_id`),
  KEY `tests_doctorcomc2ctest_call_id` (`call_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tests_doctorcomc2ctest`
--

LOCK TABLES `tests_doctorcomc2ctest` WRITE;
/*!40000 ALTER TABLE `tests_doctorcomc2ctest` DISABLE KEYS */;
/*!40000 ALTER TABLE `tests_doctorcomc2ctest` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tests_doctorcompagertest`
--

DROP TABLE IF EXISTS `tests_doctorcompagertest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tests_doctorcompagertest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tester_id` int(11) NOT NULL,
  `page_id` int(11) DEFAULT NULL,
  `success` int(11) NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tests_doctorcompagertest_tester_id` (`tester_id`),
  KEY `tests_doctorcompagertest_page_id` (`page_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tests_doctorcompagertest`
--

LOCK TABLES `tests_doctorcompagertest` WRITE;
/*!40000 ALTER TABLE `tests_doctorcompagertest` DISABLE KEYS */;
/*!40000 ALTER TABLE `tests_doctorcompagertest` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tests_doctorcomsmstest`
--

DROP TABLE IF EXISTS `tests_doctorcomsmstest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tests_doctorcomsmstest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tester_id` int(11) NOT NULL,
  `message_id` int(11) DEFAULT NULL,
  `success` int(11) NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tests_doctorcomsmstest_tester_id` (`tester_id`),
  KEY `tests_doctorcomsmstest_message_id` (`message_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tests_doctorcomsmstest`
--

LOCK TABLES `tests_doctorcomsmstest` WRITE;
/*!40000 ALTER TABLE `tests_doctorcomsmstest` DISABLE KEYS */;
/*!40000 ALTER TABLE `tests_doctorcomsmstest` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tests_twiliocallgathertest`
--

DROP TABLE IF EXISTS `tests_twiliocallgathertest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tests_twiliocallgathertest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tester_id` int(11) NOT NULL,
  `callid` varchar(34) COLLATE utf8_unicode_ci DEFAULT NULL,
  `debug_data` longtext COLLATE utf8_unicode_ci NOT NULL,
  `success` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tests_twiliocallgathertest_tester_id` (`tester_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tests_twiliocallgathertest`
--

LOCK TABLES `tests_twiliocallgathertest` WRITE;
/*!40000 ALTER TABLE `tests_twiliocallgathertest` DISABLE KEYS */;
/*!40000 ALTER TABLE `tests_twiliocallgathertest` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tests_twiliorecordtest`
--

DROP TABLE IF EXISTS `tests_twiliorecordtest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tests_twiliorecordtest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tester_id` int(11) NOT NULL,
  `callid` varchar(34) COLLATE utf8_unicode_ci DEFAULT NULL,
  `recordingurl` longtext COLLATE utf8_unicode_ci,
  `debug_data` longtext COLLATE utf8_unicode_ci NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tests_twiliorecordtest_tester_id` (`tester_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tests_twiliorecordtest`
--

LOCK TABLES `tests_twiliorecordtest` WRITE;
/*!40000 ALTER TABLE `tests_twiliorecordtest` DISABLE KEYS */;
/*!40000 ALTER TABLE `tests_twiliorecordtest` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2012-11-22  8:20:52
