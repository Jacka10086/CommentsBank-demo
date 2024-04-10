-- 创建 'users' 表
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `password` VARCHAR(255) NOT NULL
);

-- 创建 'bank' 表，存储可供选择的评论
CREATE TABLE IF NOT EXISTS `Comments_bank` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `content` TEXT NOT NULL
);

-- 创建 'abstracts' 表
CREATE TABLE IF NOT EXISTS `abstracts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `content` TEXT NOT NULL
);

-- 创建 'abstracts_comments' 表
CREATE TABLE IF NOT EXISTS `abstracts_comments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `abstract_id` INT NOT NULL,
    `comment` TEXT NOT NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
    FOREIGN KEY (`abstract_id`) REFERENCES `abstracts`(`id`)
);

-- 创建 'introductory_materials' 表
CREATE TABLE IF NOT EXISTS `introductory_materials` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `content` TEXT NOT NULL
);

-- 创建 'introductory_comments' 表
CREATE TABLE IF NOT EXISTS `introductory_comments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `intro_material_id` INT NOT NULL,
    `comment` TEXT NOT NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
    FOREIGN KEY (`intro_material_id`) REFERENCES `introductory_materials`(`id`)
);
