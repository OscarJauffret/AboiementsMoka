create database if not exists MokaDB;

use MokaDB;

create table if not exists KnownBarks (
    id int primary key auto_increment,
    bark_id int not null,
    harmonic int not null,
    amplitude float not null,
    unique (bark_id, harmonic, amplitude)
);

create table if not exists Parameters (
    id int primary key auto_increment,
    name varchar(255) not null,
    value float not null,
    unique (name)
);
