# ************************************************************
# Sequel Pro SQL dump
# Version 4541
#
# http://www.sequelpro.com/
# https://github.com/sequelpro/sequelpro
#
# Host: 127.0.0.1 (MySQL 5.7.17)
# Database: cryptoverse_starlog
# Generation Time: 2017-06-14 02:52:28 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# Dump of table block_data
# ------------------------------------------------------------

DROP TABLE IF EXISTS `block_data`;

CREATE TABLE `block_data` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `block_id` int(11) unsigned DEFAULT NULL,
  `uri` varchar(1024) DEFAULT '',
  `data` mediumblob,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table block_events
# ------------------------------------------------------------

DROP TABLE IF EXISTS `block_events`;

CREATE TABLE `block_events` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `block_hash` char(64) DEFAULT NULL,
  `block_id` int(11) unsigned DEFAULT NULL,
  `event_hash` char(64) DEFAULT NULL,
  `event_id` int(10) unsigned DEFAULT NULL,
  `chain_index_id` int(11) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table blocks
# ------------------------------------------------------------

DROP TABLE IF EXISTS `blocks`;

CREATE TABLE `blocks` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `hash` char(64) DEFAULT NULL,
  `previous_hash` char(64) DEFAULT NULL,
  `previous_id` int(11) unsigned DEFAULT NULL,
  `height` int(11) unsigned DEFAULT NULL,
  `size` int(11) unsigned DEFAULT NULL,
  `version` int(11) unsigned DEFAULT NULL,
  `difficulty` int(11) unsigned DEFAULT NULL,
  `time` int(11) unsigned DEFAULT NULL,
  `interval_id` int(11) unsigned DEFAULT NULL,
  `root_id` int(11) unsigned DEFAULT NULL,
  `chain` int(11) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table chains
# ------------------------------------------------------------

DROP TABLE IF EXISTS `chains`;

CREATE TABLE `chains` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `block_id` int(11) unsigned DEFAULT NULL,
  `block_hash` char(64) DEFAULT NULL,
  `chain` int(11) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table event_data
# ------------------------------------------------------------

DROP TABLE IF EXISTS `event_data`;

CREATE TABLE `event_data` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `event_id` int(11) unsigned DEFAULT NULL,
  `uri` varchar(1024) DEFAULT '',
  `data` mediumblob,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table event_model_types
# ------------------------------------------------------------

DROP TABLE IF EXISTS `event_model_types`;

CREATE TABLE `event_model_types` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` char(16) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table event_models
# ------------------------------------------------------------

DROP TABLE IF EXISTS `event_models`;

CREATE TABLE `event_models` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `type_id` int(11) unsigned DEFAULT NULL,
  `event_id` int(11) unsigned DEFAULT NULL,
  `usage_id` int(11) unsigned DEFAULT NULL,
  `key` char(64) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table event_pool
# ------------------------------------------------------------

DROP TABLE IF EXISTS `event_pool`;

CREATE TABLE `event_pool` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `hash` char(64) DEFAULT NULL,
  `fleet_hash` char(64) DEFAULT NULL,
  `time` int(11) unsigned DEFAULT NULL,
  `size` int(11) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table event_types
# ------------------------------------------------------------

DROP TABLE IF EXISTS `event_types`;

CREATE TABLE `event_types` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` char(16) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table event_usages
# ------------------------------------------------------------

DROP TABLE IF EXISTS `event_usages`;

CREATE TABLE `event_usages` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` char(16) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;




/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
