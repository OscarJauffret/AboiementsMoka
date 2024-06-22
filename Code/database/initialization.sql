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

create table if not exists Barks (
    id int primary key auto_increment,
    date timestamp not null,
    mode enum('Automatic', 'Manual', 'Not handled') not null,
    voice enum('Papa', 'Maman', 'Héloïse', 'Oscar', 'Augustine') not null
);