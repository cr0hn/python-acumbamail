# Acumbamail SDK Examples

This directory contains comprehensive examples demonstrating how to use the Acumbamail SDK for Python. Each example focuses on different aspects of email marketing automation and provides practical, production-ready code patterns.

## 📋 Available Examples

### 🚀 Basic Examples

#### `sync_example.py`
**Purpose**: Basic synchronous client usage
- Initialize the client
- Create mailing lists
- Add subscribers
- Create and send campaigns
- Send single emails

**Best for**: Getting started with the SDK

#### `async_example.py`
**Purpose**: Asynchronous client usage with modern Python patterns
- Context manager usage
- Async/await patterns
- Alternative client initialization
- Error handling in async context

**Best for**: High-performance applications and modern Python development

### 📊 Advanced Analytics

#### `campaign_analytics.py`
**Purpose**: Comprehensive campaign performance analysis
- Campaign performance metrics calculation
- Click analysis and URL performance
- Opener analysis by demographics
- Bounce analysis and troubleshooting
- Automated reporting generation

**Features**:
- Performance assessment with benchmarks
- Geographic and device analysis
- Detailed click tracking
- Bounce reason categorization
- Comprehensive reporting

**Best for**: Marketing teams and data analysts

### 📦 Bulk Operations

#### `bulk_operations.py`
**Purpose**: Efficient bulk data processing
- Bulk subscriber addition with error handling
- Multiple campaign creation
- Batch single email sending
- Sample data generation
- Progress tracking and reporting

**Features**:
- Rate limiting protection
- Error categorization and reporting
- Success/failure tracking
- Sample data generation for testing
- Comprehensive result summaries

**Best for**: Data migration and large-scale operations

### 🧪 A/B Testing

#### `ab_testing.py`
**Purpose**: Complete A/B testing framework for email campaigns
- Subject line testing
- Content testing
- Send time optimization
- Statistical analysis
- Winner determination

**Features**:
- Multiple variant support
- Automated winner selection
- Comprehensive reporting
- Metric-based analysis
- Template-based test creation

**Best for**: Marketing optimization and conversion improvement

### 🤖 Automated Workflows

#### `automated_workflows.py`
**Purpose**: Email automation and workflow management
- Welcome series implementation
- Drip campaign creation
- Triggered email system
- Template-based automation
- Event-driven email sending

**Features**:
- Welcome series with delayed sending
- Lead nurturing drip campaigns
- Event-triggered emails
- Template system for common scenarios
- Workflow management classes

**Best for**: Marketing automation and customer lifecycle management

### 🛡️ Error Handling

#### `error_handling.py`
**Purpose**: Robust error handling and reliability patterns
- Retry logic with exponential backoff
- Circuit breaker pattern
- Graceful degradation
- Comprehensive error categorization
- Safe client wrapper

**Features**:
- Configurable retry strategies
- Error type categorization
- Circuit breaker implementation
- Bulk operation error handling
- Logging and monitoring

**Best for**: Production applications requiring high reliability

## 🚀 Quick Start

### Prerequisites

1. **Install the SDK**:
   ```bash
   pip install acumbamail
   ```

2. **Set up your API token**:
   ```bash
   export ACUMBAMAIL_AUTH_TOKEN="your-api-token-here"
   ```

3. **Get your API token**:
   - Log into your Acumbamail account
   - Go to Settings → API
   - Copy your API token

### Running Examples

Each example can be run independently:

```bash
# Basic usage
python examples/sync_example.py
python examples/async_example.py

# Advanced features
python examples/campaign_analytics.py
python examples/bulk_operations.py
python examples/ab_testing.py
python examples/automated_workflows.py
python examples/error_handling.py
```

## 📚 Example Categories

### For Beginners
Start with these examples to understand the basics:
- `sync_example.py` - Learn the fundamentals
- `async_example.py` - Understand async patterns

### For Marketing Teams
These examples focus on campaign management and optimization:
- `campaign_analytics.py` - Performance analysis
- `ab_testing.py` - Optimization and testing
- `automated_workflows.py` - Marketing automation

### For Developers
These examples show advanced patterns and best practices:
- `bulk_operations.py` - Data processing at scale
- `error_handling.py` - Production-ready error handling
- `async_example.py` - Modern Python patterns

### For Data Analysts
Focus on analytics and reporting:
- `campaign_analytics.py` - Comprehensive reporting
- `ab_testing.py` - Statistical analysis
- `bulk_operations.py` - Data processing

## 🔧 Customization

All examples are designed to be easily customizable:

1. **Modify configuration**: Update sender information, list names, etc.
2. **Adjust timing**: Change delays, scheduling, and retry intervals
3. **Add features**: Extend examples with your specific requirements
4. **Integrate**: Use example code in your own applications

## ⚠️ Important Notes

### Test Environment
- Examples may create test data in your Acumbamail account
- Use with caution in production environments
- Consider using a test account for experimentation

### Rate Limiting
- Examples include rate limiting protection
- Be mindful of API limits in production
- Use bulk operations for large datasets

### Error Handling
- Examples demonstrate proper error handling
- Always implement error handling in production
- Monitor and log errors appropriately

## 🎯 Use Cases

### E-commerce
- Order confirmations (`automated_workflows.py`)
- Abandoned cart emails (`automated_workflows.py`)
- Product recommendations (`bulk_operations.py`)

### SaaS Applications
- Welcome series (`automated_workflows.py`)
- Feature announcements (`bulk_operations.py`)
- User onboarding (`automated_workflows.py`)

### Marketing Agencies
- A/B testing campaigns (`ab_testing.py`)
- Campaign performance analysis (`campaign_analytics.py`)
- Bulk client communications (`bulk_operations.py`)

### Content Marketing
- Newsletter management (`bulk_operations.py`)
- Content promotion (`automated_workflows.py`)
- Audience segmentation (`bulk_operations.py`)

## 🤝 Contributing

When adding new examples:

1. **Follow the existing pattern**: Use similar structure and documentation
2. **Include comprehensive comments**: Explain the purpose and usage
3. **Add error handling**: Demonstrate best practices
4. **Update this README**: Document new examples
5. **Test thoroughly**: Ensure examples work correctly

## 📞 Support

If you encounter issues with the examples:

1. Check the main SDK documentation
2. Verify your API token is correct
3. Ensure you have the required dependencies
4. Review error messages for guidance
5. Check the Acumbamail API documentation

## 📄 License

These examples are provided under the same license as the main SDK (MIT License). 