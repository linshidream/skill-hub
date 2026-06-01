package com.example.agent.skills;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import org.springframework.core.io.Resource;
import org.springframework.core.io.support.ResourcePatternResolver;
import org.springframework.stereotype.Component;

@Component
public class SkillResourceLoader {

    private final ResourcePatternResolver resourcePatternResolver;

    public SkillResourceLoader(ResourcePatternResolver resourcePatternResolver) {
        this.resourcePatternResolver = resourcePatternResolver;
    }

    public List<SkillDocument> loadSkillDocuments(String locationPattern) throws IOException {
        Resource[] resources = resourcePatternResolver.getResources(locationPattern);
        List<SkillDocument> documents = new ArrayList<>();

        for (Resource resource : resources) {
            if (!resource.exists() || !resource.isReadable()) {
                continue;
            }
            String content = resource.getContentAsString(StandardCharsets.UTF_8);
            documents.add(new SkillDocument(resource.getDescription(), content));
        }

        return documents;
    }

    public record SkillDocument(String source, String content) {
    }
}
