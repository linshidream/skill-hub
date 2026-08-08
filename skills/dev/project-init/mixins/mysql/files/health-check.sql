-- mysql 健康检查表 + 种子数据（/health 端点的 mysql 检查依赖此表）
-- 一次性运维操作：建表后执行 INSERT；生产用环境变量传密码（-a "$MYSQL_PASSWORD"，密码不入命令历史）。
-- /health 的 mysql 检查 SELECT COUNT(*) FROM t_health_check，建表+INSERT 后返回 1，确认连通+表存在+可读。

CREATE TABLE IF NOT EXISTS t_health_check (
  id           BIGINT       NOT NULL AUTO_INCREMENT,
  service_name VARCHAR(64)  NOT NULL,
  status       VARCHAR(16)  NOT NULL,
  message      VARCHAR(255),
  create_time  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO t_health_check (service_name, status, message)
VALUES ('system', 'UP', 'table initialized');
