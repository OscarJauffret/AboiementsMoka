use mokadb;

-- Insert data into the KnownBarks table

insert into KnownBarks (bark_id, harmonic, amplitude) values (1, 11, 1);

insert into KnownBarks (bark_id, harmonic, amplitude) values (2, 7, 0.1);
insert into KnownBarks (bark_id, harmonic, amplitude) values (2, 8, 0.14);
insert into KnownBarks (bark_id, harmonic, amplitude) values (2, 9, 0.24);
insert into KnownBarks (bark_id, harmonic, amplitude) values (2, 10, 1.0);
insert into KnownBarks (bark_id, harmonic, amplitude) values (2, 11, 0.42);
insert into KnownBarks (bark_id, harmonic, amplitude) values (2, 12, 0.16);

insert into KnownBarks (bark_id, harmonic, amplitude) values (3, 17, 0.1);
insert into KnownBarks (bark_id, harmonic, amplitude) values (3, 18, 0.15);
insert into KnownBarks (bark_id, harmonic, amplitude) values (3, 19, 0.24);
insert into KnownBarks (bark_id, harmonic, amplitude) values (3, 20, 0.64);
insert into KnownBarks (bark_id, harmonic, amplitude) values (3, 21, 1.0);
insert into KnownBarks (bark_id, harmonic, amplitude) values (3, 22, 0.28);
insert into KnownBarks (bark_id, harmonic, amplitude) values (3, 23, 0.16);
insert into KnownBarks (bark_id, harmonic, amplitude) values (3, 24, 0.11);

select * from KnownBarks;

insert into Parameters (name, value) values ('noise_threshold', 10.0);
insert into Parameters (name, value) values ('resemblance_threshold', 0.7);
insert into Parameters (name, value) values ('cooldown', 120);

update Parameters set value = 0.8 where name = 'resemblance_threshold';