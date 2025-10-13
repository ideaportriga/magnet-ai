"""Test script for Documentation plugin

This script tests the Documentation knowledge source plugin
by attempting to crawl a VitePress documentation site.
"""

import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


async def test_documentation_plugin():
    """Test the documentation plugin"""
    try:
        from core.plugins.registry import PluginRegistry
        from core.plugins.plugin_types import PluginType

        # Import plugins to trigger registration
        import plugins.builtin.knowledge_source  # noqa: F401

        logger.info("Testing Documentation Plugin")
        logger.info("=" * 60)

        # Get the plugin
        plugin = PluginRegistry.get(PluginType.KNOWLEDGE_SOURCE, "Documentation")
        
        if not plugin:
            logger.error("Documentation plugin not found!")
            return False

        logger.info(f"Plugin found: {plugin.metadata.name} v{plugin.metadata.version}")
        logger.info(f"Description: {plugin.metadata.description}")
        logger.info(f"Author: {plugin.metadata.author}")
        
        # Test configuration
        source_config = {
            "base_url": "http://localhost:5173",
            "languages": ["en"],
            "sections": ["admin"],
            "section_start_urls": {
                "admin": "http://localhost:5173/docs/en/admin/connect/models/overview.html"
            },
            "max_depth": 2,  # Limited depth for testing
        }
        
        collection_config = {
            "chunking": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
            }
        }

        logger.info("Creating processor...")
        processor = await plugin.create_processor(
            source_config=source_config,
            collection_config=collection_config,
            store=None,  # Not needed for basic test
        )

        logger.info("Loading data (crawling documentation)...")
        logger.info("NOTE: Make sure VitePress is running at http://localhost:5173")
        
        await processor.load_data()

        # Get metadata
        metadata = processor.get_all_records_basic_metadata()
        logger.info(f"Found {len(metadata)} documentation pages")

        if metadata:
            logger.info("\nFirst 5 pages:")
            for i, meta in enumerate(metadata[:5], 1):
                logger.info(f"  {i}. {meta.title}")
                logger.info(f"     URL: {meta.source_id}")

            # Test creating chunks from first document
            if metadata:
                logger.info(f"\nTesting chunk creation for: {metadata[0].title}")
                chunks = await processor.create_chunks_from_doc(metadata[0].source_id)
                logger.info(f"Created {len(chunks)} chunks")
                
                if chunks:
                    logger.info("\nFirst chunk preview:")
                    first_chunk = chunks[0]
                    content_preview = first_chunk.content[:200] + "..." if len(first_chunk.content) > 200 else first_chunk.content
                    logger.info(f"Content: {content_preview}")
                    logger.info(f"Metadata: {first_chunk.metadata}")

        logger.info("\n" + "=" * 60)
        logger.info("Test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_documentation_plugin())
    sys.exit(0 if success else 1)
