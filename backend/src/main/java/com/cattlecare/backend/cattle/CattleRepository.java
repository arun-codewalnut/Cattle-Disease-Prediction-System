package com.cattlecare.backend.cattle;

import org.springframework.data.jpa.repository.JpaRepository;

public interface CattleRepository extends JpaRepository<Cattle, Long> {
}
