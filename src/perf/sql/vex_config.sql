/*
 Navicat MySQL Data Transfer

 Source Server         : localhost
 Source Server Version : 50713
 Source Host           : localhost
 Source Database       : vex

 Target Server Version : 50713
 File Encoding         : utf-8

 Date: 10/11/2016 17:45:44 PM
*/

SET NAMES utf8;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
--  Table structure for `vex_config`
-- ----------------------------
DROP TABLE IF EXISTS `vex_config`;
CREATE TABLE `vex_config` (
  `project_name` varchar(255) NOT NULL,
  `test_case_type` varchar(255) NOT NULL,
  `test_case_config` varchar(255) DEFAULT NULL,
  UNIQUE KEY `project_name` (`project_name`,`test_case_type`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
--  Records of `vex_config`
-- ----------------------------
BEGIN;
INSERT INTO `vex_config` VALUES ('vex1', 'VOD_T6', '{\"test.case.name\":\"vod_perf_1\"}');
COMMIT;

SET FOREIGN_KEY_CHECKS = 1;
