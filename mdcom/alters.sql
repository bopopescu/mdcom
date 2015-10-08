BEGIN;

ALTER TABLE `MHLUsers_mhluser` 
    DROP FOREIGN KEY `partner_creator_id_refs_id_2275a059` ,
    DROP COLUMN `partner_creator_id`;

DROP TABLE `Partners_partnerip`;
DROP TABLE `Partners_partnerlog`;
DROP TABLE `Partners_partneraccounts`;
DROP TABLE `Partners_partner`;

-- add by xlin 20130624 add MHLUsers_provider fields 'certification'
ALTER TABLE `MHLUsers_provider` ADD COLUMN `certification` longtext COLLATE utf8_unicode_ci DEFAULT NULL;

-- add by htian 20130624 add refer fields
ALTER TABLE `Messaging_messagerefer` ADD COLUMN `previous_name` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE `Messaging_messagerefer` ADD COLUMN `email` varchar(64) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE `Messaging_messagerefer` ADD COLUMN `notes` longtext COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE `Messaging_messagerefer` ADD COLUMN `home_phone_number` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE `Messaging_messagerefer` ADD COLUMN `mrn` varchar(30) COLLATE utf8_unicode_ci NOT NULL;
ALTER TABLE `Messaging_messagerefer` ADD COLUMN `ssn` varchar(30) COLLATE utf8_unicode_ci NOT NULL;
ALTER TABLE `Messaging_messagerefer` ADD COLUMN `prior_authorization_number` varchar(30) COLLATE utf8_unicode_ci NOT NULL;
ALTER TABLE `Messaging_messagerefer` ADD COLUMN `other_authorization` varchar(200) COLLATE utf8_unicode_ci NOT NULL;
ALTER TABLE `Messaging_messagerefer` ADD COLUMN `internal_tracking_number` varchar(30) COLLATE utf8_unicode_ci NOT NULL;
ALTER TABLE `Messaging_messagerefer` ADD COLUMN `address` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE `Messaging_messagerefer` ADD COLUMN `icd_code` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE `Messaging_messagerefer` ADD COLUMN `ops_code` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE `Messaging_messagerefer` ADD COLUMN `medication_list` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE `Messaging_messagerefer` MODIFY COLUMN `gender` varchar(1) NULL;


-- add by mwang 20130711 add MHLUsers_mhluser fields 'refer_forward'
ALTER TABLE `MHLUsers_mhluser` ADD COLUMN `refer_forward` int(11) DEFAULT 1 NOT NULL;

-- add by dlu 20130715 alter Messaging_messagerefer fields 'phone_number','other_authorization','internal_tracking_number' allow null
ALTER TABLE `Messaging_messagerefer` MODIFY COLUMN `phone_number` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE `Messaging_messagerefer` MODIFY COLUMN `other_authorization` varchar(200) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE `Messaging_messagerefer` MODIFY COLUMN `internal_tracking_number` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE `Messaging_messagerefer` MODIFY COLUMN `prior_authorization_number` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE `Messaging_messagerefer` MODIFY COLUMN `ssn` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL;


-- add by dlu 20130805 add field 'title' on 'Mhlusers_mhluser'
AlTER TABLE `MHLUsers_mhluser` ADD COLUMN `title` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL;
COMMIT;
